# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import logging
import hashlib

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from ._featurefilters import FeatureFilter


class TargetingException(Exception):
    """
    Exception raised when the targeting filter is not configured correctly
    """


class TimeWindowFilter(FeatureFilter):
    """
    Feature Filter that determines if the current time is within the time window
    """

    def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :keyword Mapping context: Mapping with the Start and End time for the feature flag
        :paramtype context: Mapping
        :return: True if the current time is within the time window
        :rtype: bool
        """
        start = context.get("parameters", {}).get("Start")
        end = context.get("parameters", {}).get("End")

        current_time = datetime.now(timezone.utc)

        if not start and not end:
            logging.warning("%s: At least one of Start or End is required.", TimeWindowFilter.__name__)
            return False

        start_time = parsedate_to_datetime(start) if start else None
        end_time = parsedate_to_datetime(end) if end else None

        return (start_time is None or start_time <= current_time) and (end_time is None or current_time < end_time)


class TargetingFilter(FeatureFilter):
    """
    Feature Filter that determines if the user is targeted for the feature flag
    """

    @staticmethod
    def _is_targeted(context_id, rollout_percentage):
        """Determine if the user is targeted for the given context"""
        # Always return true if rollout percentage is 100
        if rollout_percentage == 100:
            return True

        hashed_context_id = hashlib.sha256(context_id.encode()).hexdigest()
        context_marker = abs(int(hashed_context_id, 16))
        percentage = (context_marker / (2**256 - 1)) * 100

        return percentage < rollout_percentage

    def _target_group(self, target_user, target_group, group, feature_flag_name):
        group_rollout_percentage = group.get("RolloutPercentage", 0)
        audience_context_id = (
            target_user + "\n" + target_group + "\n" + feature_flag_name + "\n" + group.get("Name", "")
        )

        return self._is_targeted(audience_context_id, group_rollout_percentage)

    def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :keyword Mapping context: Context for evaluating the user/group
        :paramtype context: Mapping
        :return: True if the user is targeted for the feature flag
        :rtype: bool
        """
        target_user = kwargs.pop("user", None)
        target_groups = kwargs.pop("groups", [])

        if not target_user and not (target_groups and len(target_groups) > 0):
            logging.warning("%s: Name or Groups are required parameters", TargetingFilter.__name__)
            return False

        audience = context.get("parameters", {}).get("Audience", None)
        feature_flag_name = context.get("name", None)

        if not audience:
            raise TargetingException("Audience is required for " + TargetingFilter.__name__)

        groups = audience.get("Groups", [])
        default_rollout_percentage = audience.get("DefaultRolloutPercentage", 0)

        self._validate(groups, default_rollout_percentage)

        # Check if the user is excluded
        if target_user in context.get("Exclusion", {}).get("Users", []):
            return False

        # Check if the user is in an excluded group
        for group in context.get("Exclusion", {}).get("Groups", []):
            if group.get("Name") in target_groups:
                return False

        # Check if the user is targeted
        if target_user in audience.get("Users", []):
            return True

        # Check if the user is in a targeted group
        for group in groups:
            for target_group in target_groups:
                group_name = group.get("Name", "")
                if kwargs.get("ignore_case", False):
                    target_group = target_group.lower()
                    group_name = group_name.lower()
                if group_name == target_group:
                    if self._target_group(target_user, target_group, group, feature_flag_name):
                        return True

        # Check if the user is in the default rollout
        context_id = target_user + "\n" + feature_flag_name
        return self._is_targeted(context_id, default_rollout_percentage)

    @staticmethod
    def _validate(groups, default_rollout_percentage):
        # Validate the audience settings
        if default_rollout_percentage < 0 or default_rollout_percentage > 100:
            raise TargetingException("DefaultRolloutPercentage must be between 0 and 100")

        for group in groups:
            if group.get("RolloutPercentage") < 0 or group.get("RolloutPercentage") > 100:
                raise TargetingException("RolloutPercentage must be between 0 and 100")
