# Copyright (c) 2013, 9T9IT and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from functools import partial, reduce
from toolz import compose, pluck, merge, concatv, valmap, groupby

from functools import partial
from toolz import keyfilter, compose, reduceby, merge, excepts
from pymysql.err import ProgrammingError

from frappe.utils import now, format_datetime
from functools import reduce
from toolz import merge, compose, first

def execute(filters=None):
    if cint(filters.hqm_view) and not any(
        role in ["Sales Manager", "Stock Manager", "Account Manager"]
        for role in frappe.get_roles()
    ):
        return frappe.throw(_("Insufficient permission for HQM View"))
    columns = _get_columns(filters)
    keys = compose(list, partial(pluck, "fieldname"))(columns)
    clauses, values = _get_filters(filters)
    data = with_report_error_check(_get_data)(clauses, values, keys)
    return columns, data


def _get_columns(filters):
    branches = pluck("name", frappe.get_all("Branch", filters={"disabled": 0}))
    join_columns = compose(list, concatv)
    return join_columns(
        [
            make_column("item_group", "Item Group", type="Link", options="Item Group"),
            make_column("brand", "Brand", type="Link", options="Brand"),
            make_column("warehouse", "Warehouse", type="Link", options="Warehouse"),
            make_column("item_code", "Item Code", type="Link", options="Item"),
            make_column("item_name", "Item Name", width=180),
        ],
        [make_column("cost_price", "Cost Price", type="Currency", width=90)]
        if cint(filters.hqm_view)
        else [],
        [
            make_column(
                "minimum_selling", "Minimum Selling", type="Currency", width=90
            ),
            make_column(
                "standard_selling", "Standard Selling", type="Currency", width=90
            ),
        ],
        [make_column(x, x, type="Float", width=90) for x in branches],
        [make_column("total_qty", "Total Qty", type="Float", width=90)],
        [make_column("valuation_rate", "Valuation Rate", type="Currency", width=90)],
        [make_column("total_valuation", "Total Valuation", type="Currency", width=90)]
    )


def _get_filters(filters):
    item_groups = split_to_list(filters.item_groups)
    brands = split_to_list(filters.brands)
    item_codes = split_to_list(filters.item_codes)
    clauses = concatv(
        ["i.disabled = 0"],
        ["i.item_group IN %(item_groups)s"] if item_groups else [],
        ["i.brand IN %(brands)s"] if brands else [],
        ["i.item_code IN %(item_codes)s"] if item_codes else [],
        ["INSTR(i.item_name, %(item_name)s) > 0"] if filters.item_name else [],
    )
    values = merge(
        pick(["item_name"], filters),
        {"item_groups": item_groups} if item_groups else {},
        {"brands": brands} if brands else {},
        {"item_codes": item_codes} if item_codes else {},
    )
    return " AND ".join(clauses), values


def _get_data(clauses, values, keys):
    items = frappe.db.sql(
        """
            SELECT
                i.item_group AS item_group,
                i.brand AS brand,
                i.item_code AS item_code,
                i.item_name AS item_name,
                i.valuation_rate AS valuation_rate
                b.warehouse,
                ipsb.price_list_rate AS cost_price,
                ipms.price_list_rate AS minimum_selling,
                ipss.price_list_rate AS standard_selling
            FROM `tabItem` AS i
            LEFT JOIN ({standard_buying_sq}) AS ipsb
                ON ipsb.item_code = i.item_code
            LEFT JOIN ({minimum_selling_sq}) AS ipms
                ON ipms.item_code = i.item_code
            LEFT JOIN ({standard_selling_sq}) AS ipss
                ON ipss.item_code = i.item_code
            INNER JOIN `tabBin` b
                ON i.item_code = b.item_code
            WHERE {clauses}
        """.format(
            clauses=clauses,
            standard_buying_sq=price_sq("Standard Buying"),
            minimum_selling_sq=price_sq("Minimum Selling"),
            standard_selling_sq=price_sq("Standard Selling"),
        ),
        values=values,
        as_dict=1,
    )
    bins = frappe.db.sql(
        """
            SELECT
                b.item_code AS item_code,
                b.projected_qty AS qty,
                b.projected_qty AS qty,
                w.branch AS branch,
            FROM `tabBin` AS b
            LEFT JOIN `tabBranch` AS w ON w.warehouse = b.warehouse
            WHERE b.item_code IN %(items)s
        """,
        values={"items": list(pluck("item_code", items))},
        as_dict=1,
    )

    template = reduce(lambda a, x: merge(a, {x: None}), keys, {})
    make_row = compose(
        partial(valmap, lambda x: x or None),
        partial(pick, keys),
        partial(merge, template),
        _set_qty(bins),
    )
    frappe.errprint(items)
    return with_report_generation_time([make_row(x) for x in items], keys)


def _set_qty(bins):
    grouped = groupby("item_code", bins)
    get_total = sum_by("qty")

    def fn(item):
        branches = grouped.get(item.get("item_code"))
        return (
            merge(
                item,
                {x.get("branch"): x.get("qty") for x in branches},
                {"total_qty": get_total(branches)},
            )
            if branches
            else item
        )

    return fn

def make_column(key, label=None, type="Data", options=None, width=120, hidden=0):
    return {
        "label": _(label or key.replace("_", " ").title()),
        "fieldname": key,
        "fieldtype": type,
        "options": options,
        "width": width,
        "hidden": hidden,
    }



def pick(whitelist, d):
    return keyfilter(lambda k: k in whitelist, d)


def sum_by(key):
    return compose(sum, partial(map, lambda x: x.get(key)))


def key_by(key, items):
    return reduceby(key, lambda a, x: merge(a, x), items, {})


split_to_list = excepts(
    AttributeError,
    compose(
        list,
        partial(filter, lambda x: x),
        partial(map, lambda x: x.strip()),
        lambda x: x.split(","),
    ),
    lambda x: None,
)


def with_report_error_check(data_fn):
    
    def fn(*args, **kwargs):
        try:
            return data_fn(*args, **kwargs)
        except ProgrammingError:
            return []

    return fn


mapf = compose(list, map)
map_resolved = mapf
filterf = compose(list, filter)

def with_report_generation_time(rows, keys, field=None):
    if not rows:
        return rows
    template = reduce(lambda a, x: merge(a, {x: None}), keys, {})
    get_stamp = compose(format_datetime, now)
    return [merge(template, {field or first(keys): get_stamp()})] + rows

def price_sq(price_list):
    return """
        SELECT item_code, AVG(price_list_rate) AS price_list_rate
        FROM `tabItem Price`
        WHERE price_list = '{price_list}'
        GROUP BY item_code
    """.format(
        price_list=price_list
    )
