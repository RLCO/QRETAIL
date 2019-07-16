odoo.define('store_master.master', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var config = require('web.config');
    var core = require('web.core');
    var dom = require('web.dom');
    var Dialog = require("web.Dialog");
    var Widget = require("web.Widget");
    var rpc = require("web.rpc");
    var _t = core._t;

    var SignupModal = Widget.extend({
        events: {
            'click .o_store_singup': '_onClickSignupButton',
            'change input[name="free_trail"]': '_onChangeFreeTrial',
        },
        init: function(parent, options) {
            this._super.apply(this, arguments);
            this.options = _.extend(options || {}, {
            });
        },

        start: function () {
        },

        _onClickSignupButton: function(ev) {
            var self = this;
            ev.preventDefault();
            ev.stopPropagation();
            this._dataValidation()
                .then(function () {
                    self.displayLoading();
                    self.$('#store-create-form').submit();
                })
                .fail(function () { console.log('Validation Error!') });
        },

        _onChangeFreeTrial: function() {
            console.log('fuck')
            if (this.$('input[name="free_trail"]').prop('checked') == true) {
                this.$('input[name="exp_period"]').val('free_trail')
            } else {
                this.$('input[name="exp_period"]').val('monthly');
            }
        },

        displayLoading: function () {
            var msg = _t("We are creating your retail store, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>',
                baseZ: 9999
            });
        },

        _dataValidation: function() {
            var self = this;
            var def = $.Deferred();
            this.$('.validation_error').remove();
            // 1 Email address
            var pattern = /^\w+([-+.'][^\s]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
            var email = this.$('#email').val();
            var valid = pattern.test(email);

            //password
            var password = this.$('#password').val();

            //store name
            var storePattern = /^[a-z]+$/;
            var storeName = this.$('#store_name').val();

            //phone
            var phone = this.$('#phone').val();


            if(!valid || !email) {
                this.displayError('Email', 'Email address is not valid');
                return def.reject();
            }
            if (!password) {
                this.displayError('Password', 'Please enter valid password');
                return def.reject();
            }
            if (!storeName || !storePattern.test(storeName)) {
                this.displayError('Store Name', 'Please enter valid store (a-Z)');
                return def.reject();
            }
            if (!phone) {
                this.displayError('Phone', 'Please enter valid phone number');
                return def.reject();
            }

            if (this.$('input[name="terms"]').not(':checked').length) {
                this.displayError('Terms & Conditions', 'Please accept terms & conditions');
                return def.reject();
            }

            //user name is exist or not
            ajax.jsonRpc('/check/client/exist', 'call', {'email': email, 'store': storeName}).then( function (res) {
                if (res.user) {
                    self.displayError('Email', 'User is already register with this email address! please login or use another email');
                    return def.reject();
                } else if(res.store) {
                    self.displayError('Store Name', 'Store name is already exist! please use another store name');
                    def.reject();
                }
                def.resolve();
            });
            return def;
        },

        displayError: function (title, message) {
            var messageHtml = "<div class='validation_error alert alert-danger text-center'><b style='font-size: 18px !important;'><span class='fa fa-exclamation-triangle mr4'/>"+title+"</b><div><small>"+message+"</small></div></div>";
            this.$('.validation_error').remove();
            this.$('#store-create-form').prepend($(messageHtml));
        },

    });

    $(document).ready(function() {

        $('#singup_modal').each(function () {
            var $elem = $(this);
            var form = new SignupModal(null, $elem.data());
            form.attachTo($elem);
        });

        var $model = $('#create-store');
        var $form = $model.find('form');

        $model.find('a.create_store').on('click', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();

            var res = is_all_field_value_fill();
            var pattern = /^\w+([-+.'][^\s]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
            var email = $('#email').val();
            var pat = /^[a-z]+$/;
            var storename = $('#store_name').val();
            if (pat.test(storename) == false) {
                $('.error span').text('Store name you entered is wrong, only small letter (a to z) are allowed');
                $('.error').removeClass('hide').show();
                return false;
            }
            var valid = pattern.test(email);
            if (!valid && email) {
                $('.error span').text('Email Adress you entered is wrong.')
                $('.error').removeClass('hide').show();
                return false;
            }

            if (res) {
                if ($('#term').is(':checked')) {
                    var def1 = checkStoreName($('#store_name').val());
                    var def1 = checkUserName($('#email').val());
                    $.when(def1).then(function(def1_res) {
                        if (def1_res) {
                            $('.error span').text('Either User-name or Email address already exist.')
                            $('.error').removeClass('hide').show();
                            return false;
                        }
                        $('#create-store').modal('toggle');
                        var $div = $('<div>\
                                    <h1 style="margin-top:16px;"><b>We Are Creating Your Store .. </b></h1>\
                                    <img style="margin-top:32px;" height="200px" width="200px" src="/store_master/static/src/img/loading.gif"/><br/>\
                                    <h4 style="margin-top:32px;"> <strong>Your store will be ready within few seconds ..</strong></h4></div>')
                        $.blockUI({
                            message: $div,
                            css: {
                                backgroundColor: 'rgba(19, 40, 99, 0.55)',
                                color: '#fff',
                                width: "50%",
                                left: "25%",
                                top: "35%",
                                border: 'none',
                            }
                        });
                        $form.submit();
                    });
                } else {
                    $('.error span').text('Please Accept Term And Condition To Continue.')
                    $('.error').removeClass('hide').show();
                    return false;
                }
            } else {
                $('.error span').text('Some required fields value are missign, please fill it before continue.')
                $('.error').removeClass('hide').show();
                return false;
            }
        });

        $model.find('#store_name').on('keyup', function(ev) {
            var subdomain = "smerp.ng";
            subdomain = $(this).val() + '.' + subdomain;
            $model.find('.subdomain').text(subdomain);
        });

        require('website.website');

        if (!$('#payment_method').length) {
            return $.Deferred().reject("DOM doesn't contain '#payment_method'");
        }

        // dbo note: website_sale code for payment
        // if we standardize payment somehow, this should disappear
        // When choosing an acquirer, display its Pay Now button
        var $payment = $("#payment_method");
        $payment.on("click", "input[name='acquirer']", function(ev) {
                var payment_id = $(ev.currentTarget).val();
                $("div.o_quote_acquirer_button[data-id]", $payment).addClass("hidden");
                $("div.o_quote_acquirer_button[data-id='" + payment_id + "']", $payment).removeClass("hidden");
            })
            .find("input[name='acquirer']:checked").click();

        // When clicking on payment button: create the tx using json then continue to the acquirer
        $('.o_quote_acquirer_button').on("click", 'button[type="submit"],button[name="submit"]', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var $form = $(ev.currentTarget).parents('form');
            var acquirer_id = $form.parents('.o_quote_acquirer_button').first().data('id');
            if (!acquirer_id) {
                return false;
            }
            var href = $(location).attr("href");
            var order_id = href.match(/contract\/([0-9]+)/)[1];
            var token = href.match(/contract\/[0-9]+\/([^\/?]*)/);
            token = token ? token[1] : '';
            ajax.jsonRpc('/store/' + order_id + '/transaction/' + acquirer_id + (token ? '/' + token : ''), 'call', {}).then(function(data) {
                //$form.html(data);
                //$form.submit();
                $(data).appendTo('body').submit();
            });
        });






    });

});