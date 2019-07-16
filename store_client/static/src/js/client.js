odoo.define('store_client.client', function (require) {
"use strict";

    var core = require('web.core');
    var session = require('web.session');
    var Webclient = require('web.WebClient');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;


    Webclient.include({
        events: _.extend({
            'click .oe_instance_buy': 'EzesellingPurchase',
            'click .verify_email_address': 'VerifyEmailAddress',
            'click a.oe_instance_register_show': function(ev) {$('.oe_instance_register_form').show();},
            'click #confirm_enterprise_code': 'codeSubmit',
            'click .oe_instance_hide_panel': 'hideAlert',
        }),
        show_application: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.checkExpiry();
            });
        },
        checkExpiry: function() {
            var self = this;
            $.when(
                self._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['saas_client.expiration_datetime']
                }),
                self._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['saas_client.database.secret.key']
                }),
                // self._rpc({
                //     model: 'ir.config_parameter',
                //     method: 'get_param',
                //     args: ['db.expire.date.verify']
                // }),
                self._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['saas_client.verify.email']
                }),
                'trial',
            ).then(function(dbexpiration_date, key, db_expire_date_verify, email_verification, dbexpiration_reason) {
                var is_verify_email = true;
                if (email_verification == 'not_varified') {
                    is_verify_email = false;
                }
                var today = new moment();
                dbexpiration_date = new moment(dbexpiration_date || new moment().add(30, 'd'));
                var duration = moment.duration(dbexpiration_date.diff(today));
                var options = {
                    'diffDays': Math.round(duration.asDays()),
                    'dbexpiration_reason': dbexpiration_reason,
                    'warning': 'admin',
                    //'warning': is_admin?'admin':(is_user?'user':false),
                    'key': key,
                    'email_verify': is_verify_email,
                    'db_expire_date_verify': db_expire_date_verify,
                };
                self.showAlert(options);
                console.log('hererer')
            });
        },
        showAlert: function(options) {
            var self = this;
            var hide_cookie = utils.get_cookie('oe_instance_hide_panel');
            if ((options.diffDays <= 30) || options.diffDays <= 0) {

                var expiration_panel = $(QWeb.render('ExpireNotification', {
                    has_mail: true,
                    diffDays: options.diffDays,
                    key:options.key,
                    dbexpiration_reason:options.dbexpiration_reason,
                    warning: options.warning,
                    email_verify: options.email_verify,
                }));
                expiration_panel.insertBefore($('.o_control_panel'));

                if (!options.email_verify) {
                    expiration_panel.find('.verify_email_address').on('click.widget_events', self.proxy('VerifyEmailAddress'));
                }
                if (options.diffDays <= 0) {
                    expiration_panel.children().addClass('alert-danger');
                    expiration_panel.find('a.oe_instance_register_show').on('click.widget_events', self.events['click a.oe_instance_register_show']);
                    expiration_panel.find('.oe_instance_buy').on('click.widget_events', self.proxy('EzesellingPurchase'));
                    expiration_panel.find('#confirm_enterprise_code').on('click.widget_events', self.proxy('codeSubmit'));
                    expiration_panel.find('.oe_instance_hide_panel').hide();
                    $.blockUI({message: expiration_panel,
                               css: { cursor : 'auto' },
                               overlayCSS: { cursor : 'auto' } });

                }

                if (options.email_verify)
                    return;

                var countDownDate = new Date(options.db_expire_date_verify).getTime();
                // Update the count down every 1 second
                var x = setInterval(function() {

                  // Get todays date and time
                  var now = new Date().getTime();

                  // Find the distance between now an the count down date
                  var distance = countDownDate - now;

                  // Time calculations for days, hours, minutes and seconds
                  var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                  var seconds = Math.floor((distance % (1000 * 60)) / 1000);

                  // Display the result in the element with id="demo"
                  $("#demo").html(hours + "h - " + minutes + "m - " + seconds + "s ");
                  //document.getElementById("demo").innerHTML = hours + "h - "
                  //+ minutes + "m - " + seconds + "s ";

                  // If the count down is finished, write some text 
                  if (distance < 0) {
                    clearInterval(x);
                    document.getElementById("demo").innerHTML = "STORE EXPIRED";
                    //self.RemoveStore();
                  }
                }, 1000);
            }
        },
        hideAlert: function(ev) {
            ev.preventDefault();
            utils.set_cookie('oe_instance_hide_panel', true, 24*60*60);
            $('.expire_notification_section').hide();
        },
        /** Save the registration code then triggers a ping to submit it*/
        codeSubmit: function(ev) {
            ev.preventDefault();
            var enterprise_code = $('.expire_notification_section').find('#enterprise_code').val();
            if (!enterprise_code) {
                var $c = $('#enterprise_code');
                $c.attr('placeholder', $c.attr('title')); // raise attention to input
                return;
            }
            var Master = new Model('store.master');
            self._rpc({
                model: 'store.master',
                method: 'check_enterprise_code',
                args: [enterprise_code]
            }).then(function(result) {
                utils.set_cookie('oe_instance_hide_panel', '', -1);
                if (result) {
                    console.log('result', result)
                    $.unblockUI();
                    $('.oe_instance_register').hide();
                    $('.expire_notification_section .alert').removeClass('alert-info alert-warning alert-danger');
                    $('.oe_instance_hide_panel').show();
                    $('.expire_notification_section .alert').addClass('alert-success');
                    $('.valid_date').html(moment(result.exp_date).format('LL'));
                    $('.oe_instance_success').show();
                } else {
                    $('.expire_notification_section .alert').addClass('alert-danger');
                    $('.oe_instance_error, .oe_instance_register_form').show();
                    $('#confirm_enterprise_code').html('Retry');
                }
            });
        },
        VerifyEmailAddress: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            self._rpc({
                model: 'store.master',
                method: 'send_activation_mail',
                args: []
            }).then(function(res) {
                $('.activation_email_panel').text('Verification Email Has Been Send To Your Email Adress, Please Verify It Before Expire');
            });
        },
        RemoveStore: function(ev) {
            self._rpc({
                model: 'store.master',
                method: 'remove_store',
                args: []
            }).then(function(res) {
                console.log('Store Removed Successfully');
            })
        },
        EzesellingPurchase: function(ev) {
            var limit_date = new moment().subtract(15, 'days').format("YYYY-MM-DD");
            self._rpc({
                model: 'res.users',
                method: 'search_count',
                args: [[["share", "=", false],["login_date", ">=", limit_date]]]
            }).then(function(users) {
                self._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['database.secret.key']
                }).then(function(code) {
                    self._rpc({
                        model: 'ir.config_parameter',
                        method: 'get_param',
                        args: ['master.store.id']
                    }).then(function(store_id) {
                        window.location = $.param.querystring("http://www.ezeselling.com/my/store/contract/"+store_id+"/" + code, {num_users: users});
                    });
                });
            });
        },
    })


});
