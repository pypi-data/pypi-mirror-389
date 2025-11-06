import colander
import deform

from caerp.forms import (
    range_validator,
    deferred_default_year,
    year_filter_node,
)
from caerp.forms.widgets import CleanMappingWidget
from caerp.forms.tasks.lists import PeriodSchema, AmountRangeSchema
from caerp.forms.lists import BaseListsSchema
from caerp.models.task.invoice import get_invoice_years


def get_list_schema():
    """
    Build a form schema used to list history entries
    """
    schema = BaseListsSchema().clone()
    del schema["search"]

    node = colander.SchemaNode(
        colander.String(),
        name="official_number",
        title="Numéro de facture",
        missing=colander.drop,
    )
    schema.insert(0, node)
    node = colander.SchemaNode(
        colander.Integer(),
        name="invoice_id",
        title="",
        widget=deform.widget.HiddenWidget(),
        missing=colander.drop,
    )
    schema.insert(0, node)

    node = PeriodSchema(
        name="period",
        title="",
        validator=colander.Function(
            range_validator, msg="La date de début doit précéder la date de début"
        ),
        widget=CleanMappingWidget(),
        missing=colander.drop,
    ).clone()
    node["start"].title = "Enregistré entre le"
    schema.insert(0, node)
    node = AmountRangeSchema(
        name="amount",
        title="",
        validator=colander.Function(
            range_validator,
            msg="Le montant de départ doit être inférieur ou égale "
            "à celui de la fin",
        ),
        widget=CleanMappingWidget(),
        missing=colander.drop,
    ).clone()
    node["start"].title = "Montant entre"
    schema.insert(0, node)

    node = colander.SchemaNode(
        colander.String(),
        name="action_type",
        title="Type d'action",
        widget=deform.widget.SelectWidget(
            values=(
                ("", "Tous"),
                ("ADD", "Ajout"),
                ("UPDATE", "Modification"),
                ("DELETE", "Suppression"),
            )
        ),
        missing=colander.drop,
    )
    schema.insert(0, node)

    node = year_filter_node(
        name="year",
        title="Année",
        query_func=get_invoice_years,
        default=deferred_default_year,
        default_val=("", "Tous"),
        missing=colander.drop,
    )
    schema.insert(0, node)

    return schema
