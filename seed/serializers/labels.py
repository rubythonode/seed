# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
from rest_framework import fields
from rest_framework import serializers

from seed.models import (
    CanonicalBuilding,
    StatusLabel as Label,
)


class LabelSerializer(serializers.ModelSerializer):
    organization_id = serializers.PrimaryKeyRelatedField(
        source="super_organization",
        read_only=True,
    )
    is_applied = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        """
        Labels always exist in the context of the organization they are
        assigned to.  This serializer requires that the `super_organization`
        for the label be passed into the serializer during initialization so
        that uniqueness constraints involving the `super_organization` can be
        validated by the serializer.

        """
        super_organization = kwargs.pop('super_organization')
        self.building_snapshots = kwargs.pop('building_snapshots')
        super(LabelSerializer, self).__init__(*args, **kwargs)
        if getattr(self, 'initial_data', None):
            self.initial_data['super_organization'] = super_organization.pk

    class Meta:
        fields = (
            "id",
            "name",
            "color",
            "organization_id",
            "super_organization",
            "is_applied",
        )
        extra_kwargs = {
            "super_organization": {"write_only": True},
        }
        model = Label

    def get_is_applied(self, obj):
        return self.building_snapshots.filter(
            canonical_building__labels=obj,
        ).exists()


class UpdateBuildingLabelsSerializer(serializers.Serializer):
    add_label_ids = serializers.ListSerializer(
        child=fields.IntegerField(),
        allow_empty=True,
    )
    remove_label_ids = serializers.ListSerializer(
        child=fields.IntegerField(),
        allow_empty=True,
    )

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        self.super_organization = kwargs.pop('super_organization')
        super(UpdateBuildingLabelsSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        if validated_data['add_label_ids']:
            add_labels = Label.objects.filter(
                pk__in=validated_data['add_label_ids'],
                super_organization=self.super_organization,
            )
        else:
            add_labels = []

        if validated_data['remove_label_ids']:
            remove_labels = Label.objects.filter(
                pk__in=validated_data['remove_label_ids'],
                super_organization=self.super_organization,
            )
        else:
            remove_labels = []

        for cb in self.queryset:
            cb.labels.remove(*remove_labels)
            cb.labels.add(*add_labels)

        return self.queryset


class CleansingBuildingLabelsSerializer(serializers.Serializer):
    label_ids = serializers.ListSerializer(
        child=fields.IntegerField(),
        allow_empty=True,
    )
    updates = serializers.ListSerializer(
        child=fields.DictField(),
        allow_empty=False,
    )

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        self.super_organization = kwargs.pop('super_organization')
        super(CleansingBuildingLabelsSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        labels = list(Label.objects.filter(
            pk__in=validated_data['label_ids'],
            super_organization=self.super_organization,
        ))

        # Map of label_id -> label
        label_map = {}
        for l in labels:
            label_map[l.pk] = l

        buildings = list(self.queryset)

        # Map of building_id -> building
        building_map = {}
        for b in buildings:
            building_map[b.pk] = b

        for update in validated_data['updates']:
            if update['label_id']:
                label = label_map[update['label_id']]
            else:
                label, _ = Label.objects.get_or_create(
                    name=update['label_name'],
                    color=update['label_color'],
                    super_organization=self.super_organization
                )

            # Add label to each building in add list
            for building_id in update['building_ids']:
                building = building_map[building_id]

                # Add inactive canonical building if one doesn't exist.
                if not building.canonical_building:
                    c = CanonicalBuilding.objects.create(
                        active=False,
                        canonical_snapshot=building
                    )
                    building.canonical_building = c
                    building.save()
                else:
                    c = building.canonical_building

                c.labels.add(label)

        return self.queryset
