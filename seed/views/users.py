# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""

import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from seed.decorators import ajax_request_class
from seed.lib.superperms.orgs.decorators import has_perm_class
from seed.utils.api import api_endpoint_class
from seed.utils.organizations import create_organization
from seed.landing.models import SEEDUser as User
from seed.lib.superperms.orgs.models import (
    ROLE_OWNER,
    ROLE_MEMBER,
    ROLE_VIEWER,
    Organization,
    OrganizationUser,
)
from seed.tasks import (
    invite_to_seed,
)
from django.contrib.auth.tokens import default_token_generator

_log = logging.getLogger(__name__)


def _get_role_from_js(role):
    """return the OrganizationUser role_level from the JS friendly role name

    :param role: 'member', 'owner', or 'viewer'
    :returns: int role as defined in superperms.models
    """
    roles = {
        'owner': ROLE_OWNER,
        'viewer': ROLE_VIEWER,
        'member': ROLE_MEMBER,
    }
    return roles[role]


class UserViewSet(LoginRequiredMixin, viewsets.ViewSet):

    @api_endpoint_class
    @ajax_request_class
    def retrieve(self, request, pk=None):
        """
        Retrieves the request's user's first_name, last_name, email
        and api key if exists.
        ---
        parameter_strategy: override
        parameters:
            - name: pk
              description: The ID (primary key) of the user to retrieve
              required: true
              paramType: path
        """
        """
        Returns::

            {
                'status': 'success',
                'user': {
                    'first_name': user's first name,
                    'last_name': user's last name,
                    'email': user's email,
                    'api_key': user's API key
                }
            }
        """
        try:
            user = User.objects.get(pk=pk)
        except:
            return HttpResponse("Could not retrieve user with pk = " + str(pk))
        return HttpResponse(json.dumps({
            'status': 'success',
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'api_key': user.api_key,
            }
        }))

    @api_endpoint_class
    @ajax_request_class
    @has_perm_class('requires_owner')
    def create(self, request):
        """
        Creates a new SEED user.  One of 'organization_id' or 'org_name' is needed.
        Sends invitation email to the new user.
        ---
        parameters:
            - name: organization_id
              description: The organization ID for the organization to add the user to
              required: false
              paramType: integer
            - name: org_name
              description: The name of a new organization to create for this user
              required: false
              paramType: string
            - name: first_name
              description: First name of new user
              required: true
              paramType: string
            - name: last_name
              description: Last name of new user
              required: true
              paramType: string
            - name: role
              description: The permission level of the new user within this org
              required: true
              paramType: form
              defaultValue: member
              enum: ['member', 'viewer', 'owner']
            - name: email
              description: Email address of the new user
              required: true
              paramType: string
        """
        """

        Returns::

            {
                'status': 'success',
                'message': email address of new user,
                'org': name of the new org (or existing org),
                'org_created': True if new org created,
                'username': Username of new user
            }


        """
        body = request.data
        org_name = body.get('org_name')
        org_id = body.get('organization_id')
        if ((org_name and org_id) or (not org_name and not org_id)):
            return HttpResponse(json.dumps({
                'status': 'error',
                'message': 'Choose either an existing org or provide a new one'
            }))

        first_name = body['first_name']
        last_name = body['last_name']
        email = body['email']
        username = body['email']
        user, created = User.objects.get_or_create(username=username.lower())

        if org_id:
            org = Organization.objects.get(pk=org_id)
            org_created = False
        else:
            org, _, _ = create_organization(user, org_name)
            org_created = True

        # Add the user to the org.  If this is the org's first user,
        # the user becomes the owner/admin automatically.
        # see Organization.add_member()
        if not org.is_member(user):
            org.add_member(user)
        if body.get('role') and body.get('role'):
            OrganizationUser.objects.filter(
                organization_id=org.pk,
                user_id=user.pk
            ).update(role_level=_get_role_from_js(body['role']))

        if created:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
        user.save()
        try:
            domain = request.get_host()
        except Exception:
            domain = 'buildingenergy.com'
        invite_to_seed(domain, user.email,
                       default_token_generator.make_token(user), user.pk,
                       first_name)

        return HttpResponse(json.dumps({'status': 'success', 'message': user.email, 'org': org.name,
                'org_created': org_created, 'username': user.username}))

    @api_endpoint_class
    @ajax_request_class
    @has_perm_class('requires_owner')
    @detail_route(methods=['put'])
    def update_role(self, request, pk):
        """
        Sets a user's role within an organization.
        ---
        parameter_strategy: override
        parameters:
            - name: organization_id
              description: The organization ID for the organization to update the user for
              required: true
              paramType: integer
            - name: pk
              description: The ID of the user to adjust the permission
              required: true
              paramType: path
            - name: role
              description: The new permission level of the new user within this org
              required: true
              paramType: form
              defaultValue: member
              enum: ['member', 'viewer', 'owner']
        """
        """
        Returns::

            {
                'status': 'success or error',
                'message': 'error message, if any'
            }
        """
        body = request.data
        role = _get_role_from_js(body['role'])

        user_id = pk

        organization_id = body['organization_id']

        is_last_member = not OrganizationUser.objects.filter(
            organization=organization_id,
        ).exclude(user=user_id).exists()

        if is_last_member:
            return HttpResponse(json.dumps({
                'status': 'error',
                'message': 'an organization must have at least one member'
            }))

        is_last_owner = not OrganizationUser.objects.filter(
            organization=organization_id,
            role_level=ROLE_OWNER,
        ).exclude(user=user_id).exists()

        if is_last_owner:
            return HttpResponse(json.dumps({
                'status': 'error',
                'message': 'an organization must have at least one owner level member'
            }))

        OrganizationUser.objects.filter(
            user_id=user_id,
            organization_id=body['organization_id']
        ).update(role_level=role)

        return HttpResponse(json.dumps({'status': 'success'}))

    @api_endpoint_class
    @ajax_request_class
    @detail_route(methods=['put'])
    def update_user(self, request, pk):
        """
        Updates the request's user's first name, last name, and email
        ---
        parameter_strategy: override
        parameters:
            - name: pk
              description: The ID of the user to adjust the profile
              required: true
              paramType: path
            - name: first_name
              description: The new first name of this user
              required: false
              paramType: string
            - name: last_name
              description: The new last name of this user
              required: false
              paramType: string
            - name: email
              description: The new email address of this user
              required: false
              paramType: string
        """
        """
        Returns::

            {
                'status': 'success',
                'user': {
                    'first_name': user's first name,
                    'last_name': user's last name,
                    'email': user's email,
                    'api_key': user's API key
                }
            }
        """
        body = request.data
        anything_changed = False
        if body.get('first_name'):
            request.user.first_name = body['first_name']
            anything_changed = True
        if body.get('last_name'):
            request.user.last_name = body['last_name']
            anything_changed = True
        if body.get('email'):
            request.user.email = body['email']
            request.user.username = body['email']
            anything_changed = True
        if anything_changed:
            request.user.save()
        return HttpResponse(json.dumps({
            'status': 'success',
            'user': {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'api_key': request.user.api_key,
            }
        }))