odoo.define('web_set_dashboard.client', function (require) {
"use strict";

var Widget = require('web.Widget');
var DashboardMain = require('web_settings_dashboard');

DashboardMain.Dashboard.include({

    init: function(){
        this._super.apply(this, arguments);
        this.all_dashboards.push('company');
    },

    load_company: function (data) {
        return new DashboardCompany(this, data.company).replace(this.$('.o_web_settings_dashboard_company'));
    }
});


var DashboardCompany = Widget.extend({
    template: 'DashboardCompany',

    events: {
        'click .o_setup_company': 'on_setup_company'
    },

    init: function (parent, data) {
        this.data = data;
        this.parent = parent;
        this._super.apply(this, arguments);
    },

    on_setup_company: function () {
        var self = this;
        var action = {
            type: 'ir.actions.act_window',
            res_model: 'res.company',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            res_id: this.data.company_id
        };
        this.do_action(action, {
            on_reverse_breadcrumb: function () { return self.reload(); }
        });
    },

    reload: function () {
        return this.parent.load(['company']);
    }
});


});
