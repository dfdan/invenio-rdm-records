# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Record and draft database models."""

from invenio_communities.records.records.models import CommunityRelationMixin
from invenio_db import db
from invenio_drafts_resources.records import (
    DraftMetadataBase,
    ParentRecordMixin,
    ParentRecordStateMixin,
)
from invenio_files_rest.models import Bucket
from invenio_records.models import RecordMetadataBase
from invenio_records_resources.records import FileRecordModelMixin
from sqlalchemy_utils.types import ChoiceType, UUIDType

from .systemfields.deletion_status import RecordDeletionStatusEnum


#
# Parent
#
class RDMParentMetadata(db.Model, RecordMetadataBase):
    """Metadata store for the parent record."""

    __tablename__ = "rdm_parents_metadata"


class RDMParentCommunity(db.Model, CommunityRelationMixin):
    """Relationship between parent record and communities."""

    __tablename__ = "rdm_parents_community"
    __record_model__ = RDMParentMetadata


#
# Records
#
class RDMRecordMetadata(db.Model, RecordMetadataBase, ParentRecordMixin):
    """Represent a bibliographic record metadata."""

    __tablename__ = "rdm_records_metadata"
    __parent_record_model__ = RDMParentMetadata

    # Enable versioning
    __versioned__ = {}

    bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))
    bucket = db.relationship(Bucket, foreign_keys=[bucket_id])

    media_bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))
    media_bucket = db.relationship(Bucket, foreign_keys=[media_bucket_id])

    # The deletion status is stored in the model so that we can use it in SQL queries
    deletion_status = db.Column(
        ChoiceType(RecordDeletionStatusEnum, impl=db.String(1)),
        nullable=False,
        default=RecordDeletionStatusEnum.PUBLISHED.value,
    )


class RDMFileRecordMetadata(db.Model, RecordMetadataBase, FileRecordModelMixin):
    """File associated with a record."""

    __record_model_cls__ = RDMRecordMetadata

    __tablename__ = "rdm_records_files"

    # Enable versioning
    __versioned__ = {}


class RDMMediaFileRecordMetadata(db.Model, RecordMetadataBase, FileRecordModelMixin):
    """File associated with a record."""

    __record_model_cls__ = RDMRecordMetadata

    __tablename__ = "rdm_records_media_files"

    # Enable versioning
    __versioned__ = {}


#
# Drafts
#
class RDMDraftMetadata(db.Model, DraftMetadataBase, ParentRecordMixin):
    """Draft metadata for a record."""

    __tablename__ = "rdm_drafts_metadata"
    __parent_record_model__ = RDMParentMetadata

    bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))
    bucket = db.relationship(Bucket, foreign_keys=[bucket_id])

    media_bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))
    media_bucket = db.relationship(Bucket, foreign_keys=[media_bucket_id])


class RDMFileDraftMetadata(db.Model, RecordMetadataBase, FileRecordModelMixin):
    """File associated with a draft."""

    __record_model_cls__ = RDMDraftMetadata

    __tablename__ = "rdm_drafts_files"


class RDMMediaFileDraftMetadata(db.Model, RecordMetadataBase, FileRecordModelMixin):
    """File associated with a draft."""

    __record_model_cls__ = RDMDraftMetadata

    __tablename__ = "rdm_drafts_media_files"


#
# Versions state
#
class RDMVersionsState(db.Model, ParentRecordStateMixin):
    """Store for the version state of the parent record."""

    __tablename__ = "rdm_versions_state"

    __parent_record_model__ = RDMParentMetadata
    __record_model__ = RDMRecordMetadata
    __draft_model__ = RDMDraftMetadata
