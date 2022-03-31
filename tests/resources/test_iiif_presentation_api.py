# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Universität Hamburg.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the handlers."""

from io import BytesIO

import flask_security
from invenio_accounts.testutils import login_user_via_session
from PIL import Image
from tripoli import IIIFValidator

from invenio_rdm_records.proxies import current_rdm_records


def login_user(client, user):
    """Log user in."""
    flask_security.login_user(user, remember=True)
    login_user_via_session(client, email=user.email)


def logout_user(client):
    """Log current user out."""
    flask_security.logout_user()
    with client.session_transaction() as session:
        session.pop("user_id", None)


def publish_record_with_images(
    file_id, identity, record, restricted_files=False, restricted_record=False
):
    # client_with_login will push the identity to g
    # enable files on record
    record["files"]["enabled"] = True
    if restricted_files:
        record["access"]["files"] = "restricted"

    if restricted_record:
        # TODO: how do I make a restricted record?
        ...
    # create a record with a file
    service = current_rdm_records.records_service
    draft = service.create(identity, record)
    # create a new image
    image_file = BytesIO()
    image = Image.new("RGBA", (1280, 1024), (255, 0, 0, 0))
    image.save(image_file, "png")
    image_file.seek(0)
    # add the image
    service.draft_files.init_files(draft.id, identity, data=[{"key": file_id}])
    service.draft_files.set_file_content(
        draft.id, file_id, identity, image_file
    )
    service.draft_files.commit_file(draft.id, file_id, identity)
    # publish the record
    record = service.publish(draft.id, identity)

    return record.id


def test_iiif_manifest_schema(
    running_app, es_clear, client_with_login, identity_simple, minimal_record
):
    client = client_with_login
    file_id = "test_image.png"
    recid = publish_record_with_images(
        file_id, identity_simple, minimal_record
    )
    response = client.get(f"/iiif/record:{recid}/manifest")
    manifest = response.json
    validator = IIIFValidator(fail_fast=False)
    validator.validate(manifest)
    assert not validator.errors


def test_iiif_manifest(
    running_app, es_clear, client_with_login, identity_simple, minimal_record
):
    client = client_with_login
    file_id = "test_image.png"
    recid = publish_record_with_images(
        file_id, identity_simple, minimal_record
    )
    response = client.get(f"/iiif/record:{recid}/manifest")
    assert response.status_code == 200

    manifest = response.json
    assert (
        manifest["@id"]
        == f"https://127.0.0.1:5000/api/iiif/record:{recid}/manifest"
    )
    assert manifest["label"] == "A Romans story"
    assert "sequences" in manifest
    assert len(manifest["sequences"]) == 1

    sequence = manifest["sequences"][0]
    assert (
        sequence["@id"]
        == f"https://127.0.0.1:5000/api/iiif/record:{recid}/sequence/default"
    )
    assert "canvases" in sequence
    assert len(sequence["canvases"]) == 1

    canvas = sequence["canvases"][0]
    assert (
        canvas["@id"]
        ==
        f"https://127.0.0.1:5000/api/iiif/record:{recid}/canvas/test_image.png"
    )
    assert canvas["height"] == 1024
    assert canvas["width"] == 1280
    assert "images" in canvas
    assert len(canvas["images"]) == 1

    image = canvas["images"][0]
    assert image["motivation"] == "sc:painting"
    assert image["resource"]["height"] == 1024
    assert image["resource"]["width"] == 1280
    assert (
        image["resource"]["@id"]
        ==
        f"https://127.0.0.1:5000/api/iiif/"
        f"record:{recid}:{file_id}/full/full/0/default.png"
    )
    assert (
        image["resource"]["service"]["@id"]
        ==
        f"https://127.0.0.1:5000/api/iiif/record:{recid}:{file_id}/info.json"
    )


def test_iiif_manifest_restricted_files(
    running_app,
    es_clear,
    client_with_login,
    identity_simple,
    minimal_record,
    users,
):
    client = client_with_login
    file_id = "test_image.png"
    recid = publish_record_with_images(
        file_id, identity_simple, minimal_record, restricted_files=True
    )
    logout_user(client)
    response = client.get(f"/iiif/record:{recid}/manifest")
    # TODO: should we return only the parts the user has access to?
    assert response.status_code == 403

    # Log in user and try again
    login_user(client, users[0])
    response = client.get(f"/iiif/record:{recid}/manifest")
    assert response.status_code == 200
