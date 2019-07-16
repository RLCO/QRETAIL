odoo.define('store_dashboard', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var session = require('web.session');
var webclient = require('web.web_client');

var QWeb = core.qweb;
var _t = core._t;

console.log('calledd');

var StoreDashboard = Widget.extend({
    template: 'StoreDashboardMain',

    init: function(parent, data){
        this.all_dashboards = ['user', 'store_info', 'store_service', 'store_payment'];
        return this._super.apply(this, arguments);
    },

    start: function(){
        var self = this;
        return this.load(this.all_dashboards);
    },
    update_dashboard_data: function(data, shadow) {
        var self = this;
        var deferred = new $.Deferred();
        self.rpc("/pos/dashboard/update", {filter_condition: data}, {'shadow': shadow})
        .done(function(result) {

            self.pos_gage.update_dashboard_value(result.pos_gage);
            self.custome.update_dashboard_value(result.custome);
            self.top_item.update_dashboard_value(result.top_item);
            self.payment_method.update_dashboard_value(result.payment_method);
            self.graph.update_dashboard_value(result.sales_by_hour);

            deferred.resolve();
        })
        .fail(function(err, ev) {
            if(err.code === -32098) {
                // Prevent the CrashManager to display an error
                // in case of an xhr error not due to a server error
                ev.preventDefault();
            }
        });

        return deferred;
    },
    stop_auto_refresh: function() {
        clearInterval(this.intervalNotif);
    },
    start_auto_refresh: function() {
        var self = this;
        self.intervalNotif = setInterval(function() {
            var data = {'date_filter': self.filter.date_filter, 'pos_filter': self.filter.pos_filter};
            self.update_dashboard_data(data, true);
        },  5000);
    },

    load: function(dashboards){
        var self = this;
        var loading_done = new $.Deferred();
        session.rpc("/store_dashboard/data", {}).then(function (data) {
            // Load each dashboard
            var all_dashboards_defs = [];
            _.each(dashboards, function(dashboard) {
                var dashboard_def = self['load_' + dashboard](data);
                if (dashboard_def) {
                    all_dashboards_defs.push(dashboard_def);
                }
            });

            // Resolve loading_done when all dashboards defs are resolved
            $.when.apply($, all_dashboards_defs).then(function() {
                loading_done.resolve();
            });
        });
        return loading_done;
    },

    
    load_user: function(data){
        return new StoreDashboardUser(this, data.custome).replace(this.$('.o_store_dashboard_user'));
    },
    load_store_info: function(data) {
        return new StoreInfoDashboard(this, data.store_info).replace(this.$('.o_store_info_dashboard'));
    },
    load_store_service: function(data){
        return new StoreServiceDashboard(this, data.store_service).replace(this.$('.o_store_service_dashboard'));
    },
    load_store_payment: function(data){
        return new StorePaymentDashboard(this, data.store_payment).replace(this.$('.o_store_payment_dashboard'));
    },
    // load_payment_method: function(data){
    //     return new PosDashboardPaymentMethod(this, data.payment_method).replace(this.$('.o_pos_dashboard_payment_method'));
    // },

});

var StoreDashboardUser = Widget.extend({

    template: 'StoreDashboardUser',

    init: function(parent, data){
        this.data = data;
        this._super.apply(this, arguments);
    },
    start: function(){
        this.$el.find('span.count').each(function () {
            $(this).prop('Counter', 0).animate({
                Counter: $(this).text()
            }, {
                duration: 2000,
                easing: 'swing',
                step: function (now) {
                    $(this).text(Math.ceil(now));
                }
            });
        });
        return this._super();
    },
});

var StoreInfoDashboard = Widget.extend({

    template: 'StoreInfoDashboard',

    init: function(parent, data){
        this.data = data;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
});

var StoreServiceDashboard = Widget.extend({

    template: 'StoreServiceDashboard',

    init: function(parent, data){
        this.data = data;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
});

var StorePaymentDashboard = Widget.extend({

    template: 'StorePaymentDashboard',

    init: function(parent, data){
        this.data = data;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
});


core.action_registry.add('store_dashboard.main', StoreDashboard);
});