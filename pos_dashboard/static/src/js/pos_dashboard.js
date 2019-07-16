odoo.define('pos_dashboard', function (require) {
"use strict";

var core = require('web.core');
var AbstractAction = require('web.AbstractAction');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;

var PosDashboard = AbstractAction.extend({
    template: 'PosDashboardMain',

    init: function(parent, data){
        this.all_dashboards = ['filter', 'custome', 'pos_gage', 'top_item', 'graph', 'payment_method'];
        return this._super.apply(this, arguments);
    },

    start: function(){
        var self = this;
        return this.load(this.all_dashboards);
    },
    update_dashboard_data: function(data, shadow) {
        var self = this;
        var deferred = new $.Deferred();
        self._rpc({
            route:"/pos/dashboard/update",
            params: {filter_condition: data}})
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
        self._rpc({
            route: "/pos_dashboard/data",
            params: {'filter_condition': {date_filter:'today'}}}).then(function (data) {
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

    load_filter: function(data){
        return new PosDashboardFilter(this, data.pos_gage.sales_by_pos).replace(this.$('.o_pos_dashboard_filter'));
    },
    load_custome: function(data){
        return new PosDashboardCustome(this, data.custome).replace(this.$('.o_pos_dashboard_custome'));
    },
    load_pos_gage: function(data) {
        return new PosDashboardGage(this, data.pos_gage).replace(this.$('.o_pos_dashboard_gage'));
    },
    load_top_item: function(data){
        return new PosDashboardTopItem(this, data.top_item).replace(this.$('.o_pos_dashboard_top_item'));
    },
    load_graph: function(data){
        return new PosDashboardGraph(this, data.sales_by_hour).replace(this.$('.o_pos_dashboard_graph'));
    },
    load_payment_method: function(data){
        return new PosDashboardPaymentMethod(this, data.payment_method).replace(this.$('.o_pos_dashboard_payment_method'));
    },

});

var PosDashboardCustome = Widget.extend({

    template: 'PosDashboardCustome',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.custome = this;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
    update_dashboard_value: function(data) {
        this.$el.find('.o_new_customer_value span').text(data.new_customer);
        this.$el.find('.o_repeat_customer_value span').text(data.repeat_customer);
        this.$el.find('.o_total_sale_value span').text(data.total_sales);
        this.$el.find('.o_total_transaction_value span').text(data.total_transaction);
    }
});

var PosDashboardFilter = Widget.extend({

    template: 'PosDashboardFilter',

    events: {
        "click .o_pos_dashboard_filter #start_auto_refresh": "start_auto_refresh",
        "click .o_pos_dashboard_filter #stop_auto_refresh": "stop_auto_refresh",
        "click .o_pos_dashboard_filter .date_filter button": "on_click_date_filter_button",
        "click .o_pos_dashboard_filter .filter_by_pos .dropdown-menu li a": "on_click_pos",
    },

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.filter = this;
        this.date_filter = 'today';
        this.pos_filter = 0;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
    start_auto_refresh: function() {
        this.$el.find('#start_auto_refresh').hide();
        this.$el.find('#stop_auto_refresh').show();

        this.parent.start_auto_refresh();
    },
    stop_auto_refresh: function() {
        this.$el.find('#start_auto_refresh').show();
        this.$el.find('#stop_auto_refresh').hide();

        this.parent.stop_auto_refresh();
    },
    on_click_date_filter_button: function(ev) {
        var $elem = $(ev.currentTarget);
        this.$el.find('.date_filter button').removeClass('btn-info').addClass('btn-default');
        $elem.removeClass('btn-default').addClass('btn-info');

        this.date_filter = $elem.data('date-filter');
        var data = {'date_filter': this.date_filter, 'pos_filter': this.pos_filter};
        this.parent.update_dashboard_data(data, false);

    },
    on_click_pos: function(ev) {
        var $elem = $(ev.currentTarget);
        this.$el.find('.filter_by_pos .dropdown-menu li').removeClass('active');
        this.$el.find('.filter_by_pos .dropdown-text').text($elem.text());
        $elem.parent().addClass('active');

        this.pos_filter = $elem.data('pos');
        var data = {'date_filter': this.date_filter, 'pos_filter': this.pos_filter};
        this.parent.update_dashboard_data(data, false);
    }
});

var PosDashboardGage = Widget.extend({

    template: 'PosDashboardGage',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.pos_gage = this;
        this._super.apply(this, arguments);
    },
    start: function() {
        this.setup_gage();
        return this._super();
    },
    setup_gage: function() {
        var self = this;

        // this.gage = new JustGage({
        //     parentNode: this.$el.find('#gage')[0],
        //     value: self.data.total_sales,
        //     title: 'Total Sales',
        //     min: 0,
        //     max: self.data.sales_target,

        //     titleFontColor: '#333333',
        //     valueFontColor: '#333333',
        //     labelFontColor: '#000',
        //     label: 'Sales',
        // });
        // this.gage.refresh(self.data.total_sales, self.data.sales_target);

    },
    update_dashboard_value: function(data) {
        console.log('???', data.sales_target)
        //this.gage.refresh(data.total_sales, data.sales_target);

        var $item = $(QWeb.render('TotalSalesByStore', {'widget': {'data': data}}));
        this.$el.find('.top-item tbody').empty().append($item);
    }
});

var PosDashboardTopItem = Widget.extend({

    template: 'PosDashboardTopItem',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.top_item = this;
        this._super.apply(this, arguments);
    },
    start: function(){
        return this._super();
    },
    update_dashboard_value: function(data) {
        var $top_product = $(QWeb.render('TopItem', {'widget': {'data': data}}));
        this.$el.find('.top-product').empty().append($top_product);

        var $top_cat = $(QWeb.render('TopCat', {'widget': {'data': data}}));
        this.$el.find('.top-cat').empty().append($top_cat);
    }
});

var PosDashboardPaymentMethod = Widget.extend({

    template: 'PosDashboardPaymentMethod',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.payment_method = this;
        this._super.apply(this, arguments);
    },
    start: function() {
        return this._super();
    },
    update_dashboard_value: function(data) {
        var $item = $(QWeb.render('PaymentMethod', {'widget': {'data': data}}));
        this.$el.find('.top-payment-method tbody tr').empty().append($item);
    }
});

var PosDashboardGraph = Widget.extend({

    template: 'PosDashboardGraph',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        this.parent.graph = this;
        this._super.apply(this, arguments);
    },
    start: function() {
        this.setup_bar_char()
        return this._super();
    },
    setup_bar_char: function() {
        var self = this;
        self.chart_data = '';
        nv.addGraph(function() {
            self.chart = nv.models.discreteBarChart()
            .x(function(d) { return d.label; })
            .y(function(d) { return d.value; })
            .staggerLabels(true);

            self.chart.tooltip.enabled(true);

            self.chart_data = d3.select(self.$el.find('svg')[0]).datum(self.data);
            self.chart_data.transition().duration(500).call(self.chart);

            nv.utils.windowResize(self.chart.update);
        });
    },
    update_dashboard_value: function(data) {
        this.chart_data.datum(data).transition().duration(500).call(this.chart);
        nv.utils.windowResize(this.chart.update);
    },
    get_graph_data: function() {
        var res =  [ 
            {
              key: "Cumulative Return",
              values: [
                { 
                  "label" : "0-1A" ,
                  "value" : 580
                } ,
                { 
                  "label" : "1-2A" ,
                  "value" : 700
                } , 
                { 
                  "label" : "2-3A" ,
                  "value" : 425
                } , 
                { 
                  "label" : "3-4A" ,
                  "value" : 1100
                } , 
                { 
                  "label" : "4-5A" ,
                  "value" : 600
                } , 
                { 
                  "label" : "5-6A" ,
                  "value" : 585
                } , 
                { 
                  "label" : "6-7A" ,
                  "value" : 1050
                } , 
                { 
                  "label" : "7-8A" ,
                  "value" : 1078
                } , 
                { 
                  "label" : "8-9A" ,
                  "value" : 855
                } , 
                { 
                  "label" : "9-10A" ,
                  "value" : 987
                } , 
                { 
                  "label" : "10-11A" ,
                  "value" : 785
                } , 
                { 
                  "label" : "11-12A" ,
                  "value" : 1155
                } , 
                { 
                  "label" : "0-1P" ,
                  "value" : 2000
                } , 
                { 
                  "label" : "1-2P" ,
                  "value" : 2400
                } , 
                { 
                  "label" : "2-3P" ,
                  "value" : 1145
                } , 
                { 
                  "label" : "3-4P" ,
                  "value" : 1900
                } , 
                { 
                  "label" : "4-5P" ,
                  "value" : 2100
                } , 
                { 
                  "label" : "5-6P" ,
                  "value" : 1785
                } , 
                { 
                  "label" : "6-7P" ,
                  "value" : 1652
                } , 
                { 
                  "label" : "7-8P" ,
                  "value" : 1200
                } , 
                { 
                  "label" : "8-9P" ,
                  "value" : 785
                } , 
                { 
                  "label" : "9-10P" ,
                  "value" : 658
                } , 
                { 
                  "label" : "10-11P" ,
                  "value" : 655
                } , 
                { 
                  "label" : "11-12P" ,
                  "value" : 125
                } , 
              ]
            }
          ]
        console.log('res', res)
        return res
    }
});


core.action_registry.add('pos_dashboard.main', PosDashboard);
});