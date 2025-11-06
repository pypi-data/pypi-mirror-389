"""High-level Hive API client.

This module provides ``HiveClient``, a small, synchronous authenticated
client for the Hive service. It exposes convenience methods that return
typed model objects from :mod:`src.types` and generator-based list
endpoints for memory-efficient iteration.
"""

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Generator, Optional, Sequence, TypeVar

import httpx

from .src.authenticated_hive_client import _AuthenticatedHiveClient
from .src.types.assignment import Assignment
from .src.types.assignment_response import AssignmentResponse
from .src.types.class_ import Class
from .src.types.enums.class_type_enum import ClassTypeEnum
from .src.types.exercise import Exercise
from .src.types.form_field import FormField
from .src.types.module import Module
from .src.types.program import Program
from .src.types.queue import Queue
from .src.types.subject import Subject
from .src.types.user import User

if TYPE_CHECKING:
    from .src.types.assignment import AssignmentLike
    from .src.types.core_item import HiveCoreItem
    from .src.types.exercise import ExerciseLike
    from .src.types.module import ModuleLike
    from .src.types.subject import SubjectLike

CoreItemTypeT = TypeVar("CoreItemTypeT", bound="HiveCoreItem")

ItemOrIdT = TypeVar("ItemOrIdT", bound="HiveCoreItem | int")


def resolve_item_or_id(
    item_or_id: ItemOrIdT | None,
) -> int | None:
    """Resolve a HiveCoreItem or int to an int ID."""
    from .src.types.core_item import (
        HiveCoreItem,
    )  # pylint: disable=import-outside-toplevel

    if item_or_id is None:
        return None
    if not isinstance(item_or_id, (HiveCoreItem, int)):
        raise TypeError(
            f"Expected HiveCoreItem or int, got {type(item_or_id).__name__}"
        )
    return item_or_id.id if isinstance(item_or_id, HiveCoreItem) else item_or_id


class HiveClient(_AuthenticatedHiveClient):  # pylint: disable=too-many-public-methods
    """HTTP client for accessing Hive API.

    The client is used as a context manager and provides typed helpers for
    common Hive resources (programs, subjects, modules, exercises, users,
    classes, and form fields).
    """

    def __enter__(self) -> "HiveClient":
        """Enter context manager and return this client instance.

        This delegates to the base class context manager which manages the
        underlying :class:`httpx.Client` session.
        """
        super().__enter__()
        return self

    def get_programs(
        self,
        id__in: Optional[list[int]] = None,
        program_name: Optional[str] = None,
    ) -> Generator[Program, None, None]:
        """Yield :class:`Program` objects.

        Args:
            id__in: Optional list of program ids to filter the results.

        Yields:
            Program instances parsed from the API response.
        """

        query_params = httpx.QueryParams()
        if id__in is not None:
            query_params.set("id__in", id__in)
        programs = (
            Program.from_dict(program_dict, hive_client=self)
            for program_dict in super().get(
                "/api/core/course/programs/",
                params=query_params,
            )
        )
        if program_name is not None:
            programs = filter(lambda p: p.name == program_name, programs)
        return programs

    def get_program(self, program_id: int) -> Program:
        """Return a single :class:`Program` by id.

        Args:
            program_id: The program identifier.

        Returns:
            A populated :class:`Program` object.
        """
        return Program.from_dict(
            super().get(f"/api/core/course/programs/{program_id}/"),
            hive_client=self,
        )

    def get_subjects(
        self,
        parent_program__id__in: Optional[list[int]] = None,
        subject_name: Optional[str] = None,
    ) -> Generator[Subject, None, None]:
        """Yield :class:`Subject` objects for course subjects.

        Args:
            parent_program__id__in: Optional list of parent program ids to
                filter subjects.

        Yields:
            Subject instances.
        """

        query_params = httpx.QueryParams()
        if parent_program__id__in is not None:
            query_params.set("parent_program__id__in", parent_program__id__in)
        subjects = (
            Subject.from_dict(subject_dict, hive_client=self)
            for subject_dict in super().get(
                "/api/core/course/subjects/",
                params=query_params,
            )
        )

        if subject_name is not None:
            subjects = filter(lambda s: s.name == subject_name, subjects)

        return subjects

    def get_subject(self, subject_id: int) -> Subject:
        """Return a single :class:`Subject` by id.

        Args:
            subject_id: The subject identifier.

        Returns:
            A populated :class:`Subject` object.
        """
        return Subject.from_dict(
            super().get(f"/api/core/course/subjects/{subject_id}/"),
            hive_client=self,
        )

    def get_modules(
        self,
        /,
        parent_subject__id: Optional[int] = None,
        parent_subject__parent_program__id__in: Optional[list[int]] = None,
        parent_subject: Optional["SubjectLike"] = None,
        module_name: Optional[str] = None,
    ) -> Generator[Module, None, None]:
        """Yield :class:`Module` objects for course modules.

        Args:
            parent_subject__id: Optional subject id to restrict modules.
            parent_subject__parent_program__id__in: Optional list of program
                ids to restrict modules.

        Yields:
            Module instances.
        """

        query_params = httpx.QueryParams()
        if parent_subject__parent_program__id__in is not None:
            query_params.set(
                "parent_subject__parent_program__id__in",
                parent_subject__parent_program__id__in,
            )

        parent_subject__id = (
            parent_subject__id
            if parent_subject__id is not None
            else resolve_item_or_id(parent_subject)
        )

        if parent_subject__id is not None:
            query_params.set("parent_subject__id", parent_subject__id)

        modules = (
            Module.from_dict(subject_dict, hive_client=self)
            for subject_dict in super().get(
                "/api/core/course/modules/",
                params=query_params,
            )
        )
        if module_name is not None:
            modules = filter(lambda m: m.name == module_name, modules)
        return modules

    def get_module(self, module_id: int) -> Module:
        """Return a single :class:`Module` by id.

        Args:
            module_id: The module identifier.

        Returns:
            A populated :class:`Module` object.
        """
        return Module.from_dict(
            super().get(f"/api/core/course/modules/{module_id}/"),
            hive_client=self,
        )

    def get_exercises(  # pylint: disable=too-many-arguments
        self,
        *,
        parent_module__id: Optional[int] = None,
        parent_module__parent_subject__id: Optional[int] = None,
        parent_module__parent_subject__parent_program__id__in: Optional[
            list[int]
        ] = None,
        queue__id: Optional[int] = None,
        tags__id__in: Optional[list[int]] = None,
        parent_module: Optional["ModuleLike"] = None,
        parent_subject: Optional["SubjectLike"] = None,
        exercise_name: Optional[str] = None,
    ) -> Generator[Exercise, None, None]:
        """Yield :class:`Exercise` objects.

        Accepts common filtering keyword args which are forwarded to the
        underlying list endpoint.
        """

        if parent_module is not None and parent_module__id is not None:
            assert parent_module__id == resolve_item_or_id(parent_module)
        parent_module__id = (
            parent_module__id
            if parent_module__id is not None
            else resolve_item_or_id(parent_module)
        )

        if parent_subject is not None and parent_module__parent_subject__id is not None:
            assert parent_module__parent_subject__id == resolve_item_or_id(
                parent_subject
            )
        parent_module__parent_subject__id = (
            parent_module__parent_subject__id
            if parent_module__parent_subject__id is not None
            else resolve_item_or_id(parent_subject)
        )

        exercises = self._get_core_items(
            "/api/core/course/exercises/",
            Exercise,
            parent_module__id=parent_module__id,
            parent_module__parent_subject__id=parent_module__parent_subject__id,
            parent_module__parent_subject__parent_program__id__in=parent_module__parent_subject__parent_program__id__in,
            queue__id=queue__id,
            tags__id__in=tags__id__in,
        )
        if exercise_name is not None:
            exercises = filter(lambda e: e.name == exercise_name, exercises)
        return exercises

    def get_exercise(self, exercise_id: int) -> Exercise:
        """Return a single :class:`Exercise` by id.

        Args:
            exercise_id: The exercise identifier.

        Returns:
            A populated :class:`Exercise` object.
        """
        return Exercise.from_dict(
            super().get(f"/api/core/course/exercises/{exercise_id}/"),
            hive_client=self,
        )

    def get_assignments(  # pylint: disable=too-many-arguments
        self,
        *,
        exercise__id: Optional[int] = None,
        exercise__parent_module__id: Optional[int] = None,
        exercise__parent_module__parent_subject__id: Optional[int] = None,
        exercise__tags__id__in: Optional[Sequence[int]] = None,
        queue__id: Optional[int] = None,
        user__classes__id: Optional[int] = None,
        user__classes__id__in: Optional[Sequence[int]] = None,
        user__id__in: Optional[Sequence[int]] = None,
        user__mentor__id: Optional[int] = None,
        user__mentor__id__in: Optional[Sequence[int]] = None,
        user__program__id__in: Optional[Sequence[int]] = None,
        parent_module: Optional["ModuleLike"] = None,
        parent_subject: Optional["SubjectLike"] = None,
    ) -> Generator[Assignment, None, None]:
        """Fetch assignments filtered by various optional parameters."""

        if parent_module is not None and exercise__parent_module__id is not None:
            assert exercise__parent_module__id == resolve_item_or_id(parent_module)
        exercise__parent_module__id = (
            exercise__parent_module__id
            if exercise__parent_module__id is not None
            else resolve_item_or_id(parent_module)
        )

        if (
            parent_subject is not None
            and exercise__parent_module__parent_subject__id is not None
        ):
            assert exercise__parent_module__parent_subject__id == resolve_item_or_id(
                parent_subject
            )
        exercise__parent_module__parent_subject__id = (
            exercise__parent_module__parent_subject__id
            if exercise__parent_module__parent_subject__id is not None
            else resolve_item_or_id(parent_subject)
        )

        return self._get_core_items(
            "/api/core/assignments/",
            Assignment,
            exercise__id=exercise__id,
            exercise__parent_module__id=exercise__parent_module__id,
            exercise__parent_module__parent_subject__id=exercise__parent_module__parent_subject__id,
            exercise__tags__id__in=exercise__tags__id__in,
            queue__id=queue__id,
            user__classes__id=user__classes__id,
            user__classes__id__in=user__classes__id__in,
            user__id__in=user__id__in,
            user__mentor__id=user__mentor__id,
            user__mentor__id__in=user__mentor__id__in,
            user__program__id__in=user__program__id__in,
        )

    def get_assignment(self, assignment_id: int) -> Assignment:
        """Return a single :class:`Assignment` by id.

        Args:
            assignment_id: The assignment identifier.

        Returns:
            A populated :class:`Assignment` object.
        """
        return Assignment.from_dict(
            super().get(f"/api/core/assignments/{assignment_id}/"),
            hive_client=self,
        )

    def get_users(  # pylint: disable=too-many-arguments
        self,
        *,
        classes__id__in: Optional[list[int]] = None,
        clearance__in: Optional[list[int]] = None,
        id__in: Optional[list[int]] = None,
        mentor__id: Optional[int] = None,
        mentor__id__in: Optional[list[int]] = None,
        program__id__in: Optional[list[int]] = None,
        program_checker__id__in: Optional[list[int]] = None,
    ) -> Generator[User, None, None]:
        """Yield :class:`User` objects from the management users endpoint.

        All kwargs are optional filters forwarded to the API.
        """

        return self._get_core_items(
            "/api/core/management/users/",
            User,
            classes__id__in=classes__id__in,
            clearance__in=clearance__in,
            id__in=id__in,
            mentor__id=mentor__id,
            mentor__id__in=mentor__id__in,
            program__id__in=program__id__in,
            program_checker__id__in=program_checker__id__in,
        )

    def get_user(self, user_id: int) -> User:
        """Return a single :class:`User` by id.

        Args:
            user_id: The user identifier.

        Returns:
            A populated :class:`User` object.
        """
        return User.from_dict(
            super().get(f"/api/core/management/users/{user_id}/"),
            hive_client=self,
        )

    def get_user_me(self) -> User:
        """Return the currently authenticated user.

        Returns:
            A populated :class:`User` object.
        """
        raise NotImplementedError("get_user_me() is not implemented")
        # For some reason this endpoint does not return the same data as /users/{id}/
        return User.from_dict(  # pylint: disable=unreachable
            super().get("/api/core/management/users/me/"),
            hive_client=self,
        )

    def get_classes(
        self,
        *,
        id__in: Optional[list[int]] = None,
        name: Optional[str] = None,
        program__id__in: Optional[list[int]] = None,
        type_: Optional[ClassTypeEnum] = None,
    ) -> Generator[Class, None, None]:
        """Yield :class:`Class` objects from the management classes endpoint.

        Filters may be provided as keyword arguments.
        """

        return self._get_core_items(
            "/api/core/management/classes/",
            Class,
            id__in=id__in,
            name=name,
            program__id__in=program__id__in,
            type_=type_,
        )

    def get_class(
        self,
        class_id: int,
    ) -> Class:
        """Return a single :class:`Class` by id.

        Args:
            class_id: The class identifier.

        Returns:
            A populated :class:`Class` object.
        """
        return Class.from_dict(
            super().get(f"/api/core/management/classes/{class_id}/"),
            hive_client=self,
        )

    @lru_cache(maxsize=256)
    def get_exercise_fields(
        self,
        exercise: "ExerciseLike",
    ) -> Generator[FormField, None, None]:
        """Yield :class:`FormField` objects for an exercise.

        Args:
            exercise: The exercise identifier.
        """

        exercise_id = resolve_item_or_id(exercise)

        return self._get_core_items(
            f"/api/core/course/exercises/{exercise_id}/fields/",
            FormField,
            exercise_id=exercise_id,
        )

    @lru_cache(maxsize=1024)
    def get_exercise_field(
        self,
        exercise: "ExerciseLike",
        field_id: int,
    ) -> FormField:
        """Return a single :class:`FormField` for an exercise by id.

        Args:
            exercise_id: The exercise identifier.
            field_id: The field identifier.

        Returns:
            A populated :class:`FormField` object.
        """
        exercise_id = resolve_item_or_id(exercise)
        return FormField.from_dict(
            super().get(f"/api/core/course/exercises/{exercise_id}/fields/{field_id}/"),
            hive_client=self,
        )

    def get_assignment_responses(
        self,
        assignment: "AssignmentLike",
    ) -> Generator[AssignmentResponse, None, None]:
        """Get assignment responses for a given assignment."""
        assignment_id = resolve_item_or_id(assignment)
        return self._get_core_items(
            f"/api/core/assignments/{assignment_id}/responses/",
            AssignmentResponse,
            assignment_id=assignment_id,
            extra_ctor_params={"assignment_id": assignment_id},
        )

    def get_assignment_response(
        self,
        assignment: "AssignmentLike",
        response_id: int,
    ) -> AssignmentResponse:
        """Return a single :class:`AssignmentResponse` by id."""
        assignment_id = resolve_item_or_id(assignment)
        return AssignmentResponse.from_dict(
            super().get(
                f"/api/core/assignments/{assignment_id}/responses/{response_id}/"
            ),
            assignment_id=assignment_id,
            hive_client=self,
        )

    def get_queue(self, queue_id: int):
        """Return a single :class:`Queue` by id.

        Args:
            queue_id: The queue identifier.

        Returns:
            A populated :class:`Queue` object.
        """
        return Queue.from_dict(
            super().get(f"/api/core/queues/{queue_id}/"),
            hive_client=self,
        )

    def _get_core_items(
        self,
        endpoint: str,
        item_type: type[CoreItemTypeT],
        /,
        extra_ctor_params: Optional[dict[str, Any]] = None,
        **kwargs: dict[str, Any],  # noqa: ANN401
    ) -> Generator[CoreItemTypeT, None, None]:
        """Internal helper to yield typed core items from a list endpoint.

        Args:
            endpoint: API endpoint path for the list resource.
            item_type: Model class with a ``from_dict`` constructor.
            **kwargs: Filter query parameters forwarded to the endpoint.

        Yields:
            Instances of ``item_type`` created via ``from_dict``.
        """
        if extra_ctor_params is None:
            extra_ctor_params = {}

        query_params = httpx.QueryParams()
        for name, value in kwargs.items():
            if value is not None:
                query_params = query_params.set(name, value)

        return (
            item_type.from_dict(x, **extra_ctor_params, hive_client=self)
            for x in super().get(endpoint, params=query_params)
        )

    def get_hive_version(self) -> str:
        """Return the Hive server version string."""
        data = super().get("/api/core/schema/")

        version = data.get("info", {}).get("version", "")
        if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+", version):
            raise ValueError("Invalid version string received from server")
        return version
