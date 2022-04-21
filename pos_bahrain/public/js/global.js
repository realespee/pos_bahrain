$(window).on('hashchange', page_changed);
$(window).on('load', page_changed);

async function page_changed(event) {
	// waiting for page to load completely
	frappe.after_ajax(function () {
		var route = frappe.get_route();
		var settings = await frappe.db.get_doc('Whatsapp Notification Settings')
		if (settings.enabled && route[0] == "Form") {
			frappe.ui.form.on(route[1], {
				refresh: function (frm) {
					get_settings(settings)
				}
			})

		}
	})
}

function whatsapp_notification_button(settings) {
	let cur_doc = settings.docs.find(o => o.doc_type === cur_frm.doctype);
	if (cur_doc.enabled) {
		cur_frm.add_custom_button(__("Whatsapp Notification"), function () {
			frappe.call({
				method: "latteys_nvk.api.whatsapp.create_link",
				args: {
					"doc": cur_frm.doc,
					"link_format": settings.link_format,
					"template": cur_doc.template,
					"customer": cur_doc.customer,
				},
				callback: function (r) {
					console.log(r)
					window.open(r.message)
				}
			})
		});
	}
}