// Copyright (c) 2016, 	9t9it and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Branch Stock"] = {
	"filters": [

		 {
      fieldname: 'item_groups',
      label: __('Item Group'),
      fieldtype: 'MultiSelect',
      get_data: function () {
        var item_groups = frappe.query_report.get_filter_value('item_groups') || '';

        const values = item_groups.split(/\s*,\s*/).filter((d) => d);
        const txt = item_groups.match(/[^,\s*]*$/)[0] || '';
        let data = [];

        frappe.call({
          type: 'GET',
          method: 'frappe.desk.search.search_link',
          async: false,
          no_spinner: true,
          args: {
            doctype: 'Item Group',
            txt: txt,
            filters: {
              name: ['not in', values],
            },
          },
          callback: function (r) {
            data = r.results;
          },
        });
        return data;
      },
    },

	 {
      fieldname: 'brands',
      label: __('Brands'),
      fieldtype: 'MultiSelect',
      get_data: function () {
        var brands = frappe.query_report.get_filter_value('brands') || '';

        const values = brands.split(/\s*,\s*/).filter((d) => d);
        const txt = brands.match(/[^,\s*]*$/)[0] || '';
        let data = [];

        frappe.call({
          type: 'GET',
          method: 'frappe.desk.search.search_link',
          async: false,
          no_spinner: true,
          args: {
            doctype: 'Brand',
            txt: txt,
            filters: {
              name: ['not in', values],
            },
          },
          callback: function (r) {
            data = r.results;
          },
        });
        return data;
      },
    },
	 {
      fieldname: 'item_codes',
      label: __('Item Code'),
      fieldtype: 'MultiSelect',
      get_data: function () {
        var item_codes = frappe.query_report.get_filter_value('item_codes') || '';

        const values = item_codes.split(/\s*,\s*/).filter((d) => d);
        const txt = item_codes.match(/[^,\s*]*$/)[0] || '';
        let data = [];

        frappe.call({
          type: 'GET',
          method: 'frappe.desk.search.search_link',
          async: false,
          no_spinner: true,
          args: {
            doctype: 'Item',
            txt: txt,
            filters: {
              name: ['not in', values],
            },
          },
          callback: function (r) {
            data = r.results;
          },
        });
        return data;
      },
    },

	{
                        fieldname: 'item_name',
                        label: __('Item Name'),
                        fieldtype: 'Data'
                },
                {
                        fieldname: 'hqm_view',
                        label: __('Management View'),
			fieldtype: 'Check'
		}      	

	]
};
