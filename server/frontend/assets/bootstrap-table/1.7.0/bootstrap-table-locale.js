/************************************************
*  Library: Bootstrap Table
*  - Following helpers are defines
*        - <Nothing>      
*  - Dependencies: bootstrap-table, winnum-base-ui
*
************************************************/

(function ($) {
    'use strict';
    $.fn.bootstrapTable.locales['en-US'] = {
        formatLoadingMessage: function () {
            return baseUtils.nls('Loading, please wait...');
        },
        formatRecordsPerPage: function (pageNumber) {
            return pageNumber + baseUtils.nls(' records per page');
        },
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return baseUtils.nls('Showing ') + pageFrom + baseUtils.nls(' to ') + pageTo + baseUtils.nls(' of ') + totalRows;
        },
        formatSearch: function () {
            return baseUtils.nls('Search');
        },
        formatNoMatches: function () {
            return baseUtils.nls('No matching records found');
        },
        formatPaginationSwitch: function () {
            return baseUtils.nls('Hide/Show pagination');
        },
        formatRefresh: function () {
            return baseUtils.nls('Refresh');
        },
        formatToggle: function () {
            return baseUtils.nls('Toggle');
        },
        formatColumns: function () {
            return baseUtils.nls('Columns');
        },
        formatAllRows: function () {
            return baseUtils.nls('All');
        }
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['en-US']);

})(jQuery);
