import pytest
from rest_framework.exceptions import ValidationError

from ...form.models import Document, Question
from ..validators import DocumentValidator


@pytest.mark.parametrize(
    "required_jexl,hidden_jexl,should_throw",
    [
        ("false", "true", False),
        ("false", "false", False),
        ("true", "true", False),
        ("true", "false", True),
    ],
)
def test_validate_hidden_required_field(
    db, required_jexl, hidden_jexl, should_throw, form_question, document_factory, info
):
    form_question.question.is_required = required_jexl
    form_question.question.is_hidden = hidden_jexl
    form_question.question.save()

    document = document_factory(form=form_question.form)
    error_msg = f"Questions {form_question.question.slug} are required but not provided"
    if should_throw:
        with pytest.raises(ValidationError, match=error_msg):
            DocumentValidator().validate(document, info)
    else:
        DocumentValidator().validate(document, info)


@pytest.mark.parametrize(
    "question__type,question__is_required",
    [(Question.TYPE_FILE, "false"), (Question.TYPE_DATE, "false")],
)
def test_validate_file_field(
    db, form_question, question, document_factory, answer_factory, info
):
    document = document_factory(form=form_question.form)
    answer_factory(document=document, question=question)
    DocumentValidator().validate(document, info)


@pytest.mark.parametrize(
    "required_jexl,should_throw",
    [
        ("true", True),
        ("false", False),
        ("'parent.sub_2.sub_2_question_1'|answer == 'foo'", True),
        ("'parent.sub_2.sub_2_question_1'|answer == 'bar'", False),
    ],
)
def test_validate_nested_form(
    db,
    required_jexl,
    should_throw,
    form,
    form_question_factory,
    document_factory,
    question_factory,
    answer_factory,
    answer_document_factory,
    info,
):
    sub_form_question_1 = form_question_factory(
        form__slug="sub_1",
        question__type=Question.TYPE_TEXT,
        question__is_required=required_jexl,
        question__slug="sub_1_question_1",
    )
    sub_form_question_2 = form_question_factory(
        form__slug="sub_2",
        question__type=Question.TYPE_TEXT,
        question__is_required="true",
        question__slug="sub_2_question_1",
    )

    main_form_question_1 = form_question_factory(
        question__type=Question.TYPE_FORM,
        question__sub_form=sub_form_question_1.form,
        question__slug="sub_1",
        question__is_required="false",
    )
    form_question_factory(
        form=main_form_question_1.form,
        question__type=Question.TYPE_FORM,
        question__sub_form=sub_form_question_2.form,
        question__slug="sub_2",
    )

    main_document = document_factory(form=main_form_question_1.form)

    Document.objects.create_and_link_child_documents(
        main_form_question_1.form, main_document
    )

    sub_2_document = Document.objects.filter(form__slug="sub_2").first()
    answer_factory(
        document=sub_2_document, question=sub_form_question_2.question, value="foo"
    )

    if should_throw:
        error_msg = f"Questions {sub_form_question_1.question.slug} are required but not provided"
        with pytest.raises(ValidationError, match=error_msg):
            DocumentValidator().validate(main_document, info)
    else:
        DocumentValidator().validate(main_document, info)


@pytest.mark.parametrize(
    "question__data_source,value,valid",
    [
        ("MyDataSource", "5.5", True),
        ("MyDataSource", 5.5, False),
        ("MyOtherDataSource", "5.5", True),
        ("MyOtherDataSource", 5.5, False),
        ("MyOtherDataSource", 23, False),
        ("MyDataSource", "not in data", False),
        ("MyOtherDataSource", "not in data", True),
    ],
)
@pytest.mark.parametrize(
    "question__type",
    [Question.TYPE_DYNAMIC_CHOICE, Question.TYPE_DYNAMIC_MULTIPLE_CHOICE],
)
def test_validate_dynamic_options(
    db,
    form_question,
    question,
    value,
    valid,
    document_factory,
    answer_factory,
    info,
    settings,
):
    settings.DATA_SOURCE_CLASSES = [
        "caluma.data_source.tests.data_sources.MyDataSource",
        "caluma.data_source.tests.data_sources.MyOtherDataSource",
    ]
    if question.type == Question.TYPE_DYNAMIC_MULTIPLE_CHOICE and not value == 23:
        value = [value]

    document = document_factory(form=form_question.form)
    answer_factory(value=value, document=document, question=question)
    if valid:
        DocumentValidator().validate(document, info)
    else:
        with pytest.raises(ValidationError):
            DocumentValidator().validate(document, info)
