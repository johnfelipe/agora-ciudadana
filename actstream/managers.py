from collections import defaultdict

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from actstream.gfk import GFKManager
from actstream.decorators import stream


class ActionManager(GFKManager):
    """
    Default manager for Actions, accessed through Action.objects
    """

    def public(self, *args, **kwargs):
        """
        Only return public actions
        """
        kwargs['public'] = True
        return self.filter(*args, **kwargs)

    @stream
    def actor(self, object, **kwargs):
        """
        Stream of most recent actions where object is the actor.
        Keyword arguments will be passed to Action.objects.filter
        """
        return object.actor_actions.public(**kwargs)

    @stream
    def target(self, object, **kwargs):
        """
        Stream of most recent actions where object is the target.
        Keyword arguments will be passed to Action.objects.filter
        """
        return object.target_actions.public(**kwargs)

    @stream
    def action_object(self, object, **kwargs):
        """
        Stream of most recent actions where object is the action_object.
        Keyword arguments will be passed to Action.objects.filter
        """
        return object.action_object_actions.public(**kwargs)

    @stream
    def model_actions(self, model, **kwargs):
        """
        Stream of most recent actions by any particular model
        """
        ctype = ContentType.objects.get_for_model(model)
        return self.public(
            (Q(target_content_type=ctype) |
            Q(action_object_content_type=ctype) |
            Q(actor_content_type=ctype)),
            **kwargs
        )

    @stream
    def object_actions(self, object, **kwargs):
        '''
        Stream most recent actions where object is the action_object, the target
        or even the actor.
        '''
        ctype = ContentType.objects.get_for_model(object)
        return self.public(
            (Q(target_content_type=ctype, target_object_id = object.id) |
            Q(action_object_content_type=ctype, action_object_object_id=object.id) |
            Q(actor_content_type=ctype, actor_object_id=object.id)),
            **kwargs
        )

    def election_actions(self, election, **kwargs):
        '''
        Stream most recent actions related to an election, which includes those
        related to the agora in which the election takes place where people
        delegated
        '''
        etype = ContentType.objects.get_for_model(election)
        atype = ContentType.objects.get_for_model(election.agora)

        if election.has_started() and election.has_ended():
            return self.public(
                (Q(target_content_type=etype, target_object_id = election.id) |
                Q(action_object_content_type=etype, action_object_object_id=election.id) |
                Q(actor_content_type=etype, actor_object_id=election.id) |
                Q(target_content_type=atype, verb='delegated',
                    target_object_id=election.agora.id,
                    timestamp__lt=election.voting_extended_until_date,
                    timestamp__gt=election.voting_starts_at_date)),
                **kwargs)
        elif election.has_started():
            return self.public(
                (Q(target_content_type=etype, target_object_id = election.id) |
                Q(action_object_content_type=etype, action_object_object_id=election.id) |
                Q(actor_content_type=etype, actor_object_id=election.id) |
                Q(target_content_type=atype, verb='delegated',
                    target_object_id=election.agora.id,
                    timestamp__gt=election.voting_starts_at_date)),
                **kwargs)
        else:
            return self.public(
                (Q(target_content_type=etype, target_object_id = election.id) |
                Q(action_object_content_type=etype, action_object_object_id=election.id) |
                Q(actor_content_type=etype, actor_object_id=election.id)),
                **kwargs)

    @stream
    def user(self, object, **kwargs):
        """
        Stream of most recent actions by objects that the passed User object is
        following.
        """
        from actstream.models import Follow
        q = Q()
        qs = self.filter(public=True)
        actors_by_content_type = defaultdict(lambda: [])
        others_by_content_type = defaultdict(lambda: [])

        follow_gfks = Follow.objects.filter(user=object).values_list(
            'content_type_id', 'object_id', 'actor_only')

        if not follow_gfks:
            return qs.none()

        for content_type_id, object_id, actor_only in follow_gfks.iterator():
            actors_by_content_type[content_type_id].append(object_id)
            if not actor_only:
                others_by_content_type[content_type_id].append(object_id)

        for content_type_id, object_ids in actors_by_content_type.iteritems():
            q = q | Q(
                actor_content_type=content_type_id,
                actor_object_id__in=object_ids,
            )
        for content_type_id, object_ids in others_by_content_type.iteritems():
            q = q | Q(
                target_content_type=content_type_id,
                target_object_id__in=object_ids,
            ) | Q(
                action_object_content_type=content_type_id,
                action_object_object_id__in=object_ids,
            )
        qs = qs.filter(q, **kwargs)
        return qs


class FollowManager(models.Manager):
    """
    Manager for Follow model.
    """

    def for_object(self, instance):
        """
        Filter to a specific instance.
        """
        content_type = ContentType.objects.get_for_model(instance).pk
        return self.filter(content_type=content_type, object_id=instance.pk)

    def is_following(self, user, instance):
        """
        Check if a user is following an instance.
        """
        if not user or user.is_anonymous():
            return False
        queryset = self.for_object(instance)
        return queryset.filter(user=user).exists()
