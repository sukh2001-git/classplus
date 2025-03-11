frappe.listview_settings["Student Classplus"] = {
    onload: function(listview) {
        console.log("Adding button to fetch Classplus data");
        listview.page.add_inner_button("Fetch Course Details", function() {
            // Show loading indicator
            frappe.show_alert({
                message: __("Fetching data from Classplus..."),
                indicator: 'blue'
            }, 3);

            frappe.call({
                method: "classplus.api.classplus_api.fetch_classplus_data",
                freeze: true,
                freeze_message: __("Fetching and processing Classplus data..."),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.error) {
                            frappe.msgprint({
                                title: __('Sync Failed'),
                                indicator: 'red',
                                message: __(r.message.error || 'Unable to fetch Classplus data')
                            });
                        } else {
                            let msg = r.message.message;
                            if (r.message.new_entries !== undefined && r.message.updated_entries !== undefined) {
                                msg += `<br><br>New entries: ${r.message.new_entries}<br>Updated entries: ${r.message.updated_entries}`;
                            }
                            
                            frappe.msgprint({
                                title: __('Sync Completed'),
                                indicator: 'green',
                                message: __(msg)
                            });
                            
                            frappe.ui.toolbar.clear_cache();
                        }
                    } else {
                        frappe.msgprint({
                            title: __('Sync Failed'),
                            indicator: 'red',
                            message: __('No response received from server')
                        });
                    }
                    listview.refresh();
                },
                error: function(err) {
                    console.error("Classplus sync error:", err);
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: __('An unexpected error occurred while fetching Classplus data')
                    });
                }
            });
        });
    }
};