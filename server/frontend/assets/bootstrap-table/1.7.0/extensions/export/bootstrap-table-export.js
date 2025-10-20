/**
 * @author zhixin wen <wenzhixin2010@gmail.com>
 * extensions: https://github.com/kayalshri/tableExport.jquery.plugin
 */

(function ($) {
    'use strict';

    var TYPE_NAME = {
        json: 'JSON',
        json_all: 'JSON (' + baseUtils.nls('export all rows') + ')',
        xml: 'XML',
        xml_all: 'XML (' + baseUtils.nls('export all rows') + ')',
        png: 'PNG',
        png_all: 'PNG (' + baseUtils.nls('export all rows') + ')',
        csv: 'CSV',
        csv_all: 'CSV (' + baseUtils.nls('export all rows') + ')',
        pdf: 'PDF',
        pdf_all: 'PDF (' + baseUtils.nls('export all rows') + ')',
        txt: 'TXT',
        txt_all: 'TXT (' + baseUtils.nls('export all rows') + ')',
        sql: 'SQL',
        sql_all: 'SQL (' + baseUtils.nls('export all rows') + ')',
        doc: 'DOC',
        doc_all: 'DOC - ' + baseUtils.nls('export all rows'),
        excel: 'XLS',
        excel_all: 'XLS (' + baseUtils.nls('export all rows') + ')'
    };

    $.extend($.fn.bootstrapTable.defaults, {
        showExport: false,
        exportDataType: 'all', // basic, all, selected
        exportTypes: ['txt', 'txt_all', 'excel', 'excel_all', 'png'],
        exportOptions: {}
    });

    var BootstrapTable = $.fn.bootstrapTable.Constructor,
        _initToolbar = BootstrapTable.prototype.initToolbar;

    BootstrapTable.prototype.initToolbar = function () {
        this.showToolbar = this.options.showExport;

        _initToolbar.apply(this, Array.prototype.slice.apply(arguments));

        if (this.options.showExport) {
            var that = this,
                $btnGroup = this.$toolbar.find('>.btn-group'),
                $export = $btnGroup.find('div.export');
	   var istogglePagination = false;
	   var modalId;

            if (!$export.length) {
                $export = $([
                    '<div class="export btn-group">',
                        '<button title="' + baseUtils.nls('Export table') + '" class="btn btn-default dropdown-toggle" ' +
                            'data-toggle="dropdown" type="button">',
                            '<i class="glyphicon glyphicon-export icon-share"></i> ',
                            '<span class="caret"></span>',
                        '</button>',
                        '<ul class="dropdown-menu" role="menu">',
                        '</ul>',
                    '</div>'].join('')).appendTo($btnGroup);

                var $menu = $export.find('.dropdown-menu'),
                    exportTypes = this.options.exportTypes;

                if (typeof this.options.exportTypes === 'string') {
                    var types = this.options.exportTypes.slice(1, -1).replace(/ /g, '').split(',');

                    exportTypes = [];
                    $.each(types, function (i, value) {
                        exportTypes.push(value.slice(1, -1));
                    });
                }
                $.each(exportTypes, function (i, type) {
                    if (TYPE_NAME.hasOwnProperty(type)) {
                        $menu.append(['<li data-type="' + type + '">',
                                '<a href="javascript:void(0)">',
                                    TYPE_NAME[type],
                                '</a>',
                            '</li>'].join(''));
                    }
                });

                $menu.find('li').click(function () {
                    var type = $(this).data('type'),
                        doExport = function () {
                            that.$el.tableExport($.extend({}, that.options.exportOptions, {
                                type: type,
                                escape: false
                            }));
			 if ( istogglePagination ){
			 	that.togglePagination();
			 }
			 baseUtils.closeModal(modalId);
                        };

                    if (that.options.exportDataType === 'all' && that.options.pagination) {
			if ( type.endsWith('_all') ){ 
				istogglePagination = true;
				type = type.substring(0, type.length-4);
                        		that.$el.one('load-success.bs.table', function () {
                            		doExport();
                        		});
				modalId = baseUtils.createModal('{"items":{"modelType":"1", "show":true, "modal":false, "title":"' + baseUtils.nls('Export table') + '", "body":"' + baseUtils.nls('Loading, please wait...') + '" }}');
                        		that.togglePagination();
			}else{
				istogglePagination = false;
				doExport();
			}
                    } else if (that.options.exportDataType === 'selected') {
		      istogglePagination = false;
                        var data = that.getData(),
                            selectedData = that.getAllSelections();

                        that.load(selectedData);
                        doExport();
                        that.load(data);
                    } else {
		      istogglePagination = false;
                        doExport();
                    }
                });
            }
        }
    };
})(jQuery);
