/**********************
 * See: http://jsdoc.sourceforge.net/
 **********************/

// FIXME: take advantage of jQuery 1.4+; use focusOut instead of blur where it makes sense (etc)

/** 
 * This data structure is the heart of author special mode.  It is used as a 
 * blackboard, as a display buffer, and to represent much of the state of the
 * display
 * 
 * NB: Initialization values for debug purposes only.
 */
shared_data = {
    'authors':      [ [], ],        // set of all [author, affiliation1, affiliation2 ...]
    'affiliations': [],             // list of institutions present in this data
    'affilcounts':  [],             // list of uses of institutions in affiliations list
    'paging':       {},             // dictionary for keeping track of pagination of large lists
    'folded':       [],             // which columns are currently hidden
    'row_cut':      [],             // the row recently removed from the data set with 'cut'
    'headline':     {},             // recid, paper title: used just once, at initialization
    'crs':          '',
};

/** 
 * main: this target fires as soon as the DOM is ready, which may be before
 *       the page download is complete.  Everything else is driven from here.
 */
$(document).ready(
    function() {
        var data;
        data = shared_data;

        // calculate whether to show the pagination widget
        data.paging.pages = Math.ceil(data.authors.length / data.paging.rows);

        // startup behaviors
        // $('<link rel="stylesheet" type="text/css" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/themes/redmond/jquery-ui.css" />').appendTo("head"); 
        $('<link rel="stylesheet" type="text/css" href="/img/jquery-ui.css" />').appendTo("head"); // XXX: This version is ugly.
        $.ajax({ url: "/img/bibeditauthors.css", success: function(results) {
            $("<style></style>").appendTo("head").html(results);
            }}); 
        $('#submit_button').css('display', 'inline'); // jQuery parses so make the button live

        /* Delete some of the cruft we don't care about that templates brought in to us */
        $('.pagebodystripeleft').html('').width(0).height(0);
        $('.pagebodystriperight').html('').width(0).height(0);

        $(window).keydown(function(event){ if(event.keyCode === 13) { event.preventDefault(); return false; } });
        $(window).resize(function (ev) { /* console.log("calling c_b_s from resize event set from ready"); */ calculate_box_sizes(shared_data.affiliations); });
        $(window).bind('load', function (ev) { calculate_box_sizes(shared_data.affiliations); });

        // add the pagination widget (only displays if it's needed)
        updatePaginationControls(data);

        // Tell the user the tables are loading, then go build them
        $('.headline_div').html('<h3 id="paper_title">'+shared_data.headline.recid+': '+shared_data.headline.title+'</h3>');
        $('#TableContents').html('<p id="loading_msg">Loading; please wait...</p>');
        updateTable(data);

        $(getRowSelector(0)+' .affil_box').focus();
    }
);

/**
 * Create the HTML representation of a table representing shared_data, assign
 * event handlers, and maintain folding status.
 * 
 * @param {Array} shared_data The dictionary of shared state
 */
function updateTable(shared_data) {
    // remove empty affiliation columns 
    filter_affiliations(shared_data);

    // generate table header & body
    generateTableHeader('#NonTableHeaders', shared_data.affiliations); // DEBUG NEW
    generateTableBody('#TableContents', shared_data);
    $('#TableContents').children(':even').addClass('even_row');

    // add column folding click handlers
    /* $('a.hide_link').click(       // FIXME: id selector faster?  does it matter?
            function() { 
            shared_data['folded'].push(this.name); 
            foldColumn(this.name, this.title.replace('hide', 'expand'));
            });

    // fold the columns previously checked
    for (var i in shared_data['folded']) {
        if (shared_data['folded'][i]  != null) {
            foldColumn(shared_data['folded'][i], "Click to expand.");
        }
    }
    */ // column folding disabled because it's currently broken

    // ok we've built our table up, now make everything fit!
    $(window).resize();
    return false;
}

/** 
 * Dynamically calculate a static CSS layout. Lets us have nice things like
 * individually scrolling table portions which are hard to do with fully 
 * dynamic layouts, but still have things resize nicely for different window
 * sizes.  At least, theoretically.
 */
function calculate_box_sizes(affiliations) {
    var affi_w, auth_w, column_w, header_w, form_base_w, max_header_height, plus_sign_w, rownum_w, scrollbar_padding_w, t_height, w_width, w_height;
    w_width = $(window).width();
    w_height = $(window).height();
    t_height = Math.floor(0.7 * w_height);

    form_base_w = Math.floor(0.95 * w_width);
    scrollbar_padding_w = 40;
    rownum_w = 20;
    auth_w = 120;
    affi_w = 200;
    column_w = 60;
    plus_sign_w = $('.add_row_img').width();
    max_header_height = $('.add_row_img').height(); 
    header_w = rownum_w + auth_w + affi_w + plus_sign_w + (column_w * affiliations.length + 1) + scrollbar_padding_w;

    function copy_css_h_sizing_from_to(tgfrom, tgto) {
        $(tgto).css('width', $(tgfrom).css('width')); 
        $(tgto).css('padding-right', $(tgfrom).css('padding-right')); 
        $(tgto).css('padding-left', $(tgfrom).css('padding-left')); 
    }

    $('.pageheader').remove();         // remove the headers
    $('.pagefooter').remove();         // remove the headers
    //$('#editauthors_form').width(form_base_w);
    //$('#asm_uitable').width(rownum_w + auth_w + affi_w + plus_sign_w + (column_w * (affiliations.length + 1)));
    //$('#NonTableHeaders').width( $('#asm_uitable').width() );
    $('#editauthors_form').width(Math.min(form_base_w, Math.floor(1.5 * header_w)));
    $('#asm_uitable').width(header_w);
    $('#NonTableHeaders').width(header_w);
    $('#TableContents').height(t_height);
    if (affiliations.length === 0) {
        $('NonTableContents').innerWidth(header_w);
    }

    /* Set everything in the header to the width of each thing's body element */
    $('.rownum.bodyrow').width(rownum_w);
    copy_css_h_sizing_from_to('.rownum.bodyrow', '.rownum.header')
    $('.author_box').width(auth_w);
    copy_css_h_sizing_from_to('.author_box_td', '.author_head');
    $('.affil_box').width(affi_w);
    copy_css_h_sizing_from_to('.affil_box_td', '.affil_head');
    copy_css_h_sizing_from_to('.add_row_img', '#add_row_img_spacer');
    copy_css_h_sizing_from_to('.add_row_img_container', 'add_row_img_head');
    $('.column_content.bodyrow').width(column_w);
    $('.column_content.bodyrow').each(function (idx, elem) {
        $('.column_content.header').eq(idx).width($(elem).width());
    });

    /* Set elements in header to the height of the tallest thing in the header, plus some */
    $('.column_content.header').each(function(idx, elem) { max_header_height = Math.max(($(this).height()+1), max_header_height); });
    $('.header_container').height(max_header_height);
    $('.header_container').children().height(max_header_height);
}

/* FIXME: need abstract insertRow, deleteRow, interface */

function get_id_getter() {
    var id = 1;
    return function () {
        return ++id;
    }
}
getID = get_id_getter();

function getRowNumber(box) {
    return box.parentNode.parentNode.getAttribute('row') * 1;
}

function getRowSelector(row) {
    return 'tr[row='+row+']';
}

function setRow(row, shared_data, skip_resizing) {
    var allaffiliations, rowselector, thisrowauthors;
    allaffiliations = shared_data.affiliations;
    rowselector     = getRowSelector(row);
    thisrowauthors  = shared_data.authors[row];
    $(rowselector).html(generateRowContents(row, thisrowauthors, allaffiliations));
    addHandler_currentRowHilight(rowselector + ' input[type="text"]', shared_data);
    addHandler_scrubAndSynchToAuthors(rowselector + ' .author_box', shared_data);
    addHandler_autocompleteAffiliations(rowselector + ' .affil_box', shared_data); 
    addHandler_semicolonSepBoxToAffiliations(rowselector + ' .affil_box', shared_data);
    addHandler_plusButtonAddsRow(rowselector + ' .add_row_img', shared_data);
    addHandler_keystrokesForInputBoxes(rowselector + ' input[type="text"]', shared_data);
    addHandler_checkBoxesChangeState(rowselector + ' input[type=checkbox]', shared_data);
    $(window).resize();
}

function insertRowAfter(box, shared_data) {
    var row;
    row = getRowNumber(box) + 1;
    console.log("inserting row after " + row); // DEBUG
    //shared_data['authors'].splice(row, 0, ['**new author**']); // DEBUG
    shared_data.authors.splice(row, 0, ['', '']);
    // XXX: we should be able to insert into the DOM directly and use setRow,
    //      but our current sequential numbering of rows and reliance on row
    //      numbers for selection means we must update the whole display on 
    //      every insertion.  To fix this, we should probably give rows unique
    //      ids with getID() and decouple row IDs from display order, instead 
    //      using index in shared_data.authors for display order, and having 
    //      that store the now-meaningless identifier for the row.
    updateTable(shared_data);
    updatePaginationControls(shared_data);
    $(box).blur();
    $(getRowSelector(row) + ' .author_box').focus();
} 

/**
 * Filter and sort institutional affiliation columns
 * 
 * Set column text for completely unchecked columns to ''
 * Then remove all instances of ''
 * And finally reset our counters (NB: Because our counters get reset, this requires generateTable* to be run)
 */
function filter_affiliations(shared_data) {
    for (var i = 0; i < shared_data.affilcounts.length; i++) { 
        if (!shared_data.affilcounts[i]) { shared_data.affiliations[i] = ''; } }
    shared_data['affiliations'] = shared_data['affiliations'].filter(function(x, dummy_idx, dummy_arr) { return x != ''; });
    shared_data['affiliations'].sort(function(x, y) {var a, b; a = x.toLowerCase(); b = y.toLowerCase(); if (a > b) return 1; if (b > a) return -1; return 0;});
    shared_data['affilcounts'] = [];
    return false;
}

/**
 * Determine whether the pagination widget is needed, and if it is, paint it
 * and add its event handlers.
 * 
 * // FIXME: Keystrokes left_arrow and right_arrow to go forward and back
 * // FIXME: use bookmarkable hashtag urls like in http://ajaxpatterns.org/Unique_URLs
 *
 * @param {Array} shared_data The global dictionary of shared state
 */
function updatePaginationControls(shared_data) {
    page_data = shared_data.paging;
    if (page_data.pages == 1) return;
    $('#paging_navigation').css('display', 'inline');
    var offset = page_data.offset*1;
    var rows = page_data.rows*1;
    var max_rows = shared_data.authors.length*1;
    var prev_button = '<a href="#" id="paging_button_back">previous</a>  '; 
    var status_text = 'Authors ' + (offset+1) + '-' + (offset+rows) + ' of ' + max_rows;
    status_text += ', in batches of <input type="text" id="maxRowsBox" size=4 title="If you change the value in this box and then click outside of ';
    status_text += 'it, you can change how many authors you can edit at one time." value="' + rows + '" />.';
    var next_button = '<a href="#" id="paging_button_forward">next</a>  ';
    $('#paging_navigation').html(prev_button + status_text + next_button);
    $('#paging_button_back').click(function() {
            paginated_page_back(offset, rows, max_rows, shared_data);
            return false;
    });
    $('#paging_button_forward').click(function() {
            paginated_page_forward(offset, rows, max_rows, shared_data);
            return false;
    });
    $('#maxRowsBox').change(function() {
            // TODO: instead of updateTable, calculate direction and magnitude of change and delete or insert rows
            shared_data.paging.rows = $('#maxRowsBox').val()*1;
            updateTable(shared_data);
            updatePaginationControls(shared_data);
            //return false;
    });
}

/**
 * Next page of authors
 * XXX: record params, all of these should come in as numbers
 */
function paginated_page_forward(offset, rows, max_rows, shared_data) {
    if ((offset + rows) >= max_rows) return false;
    offset += rows;
    shared_data.paging.offset = offset;
    updateTable(shared_data);
    updatePaginationControls(shared_data);
}

/**
 * Previous page of authors
 */
function paginated_page_back(offset, rows, max_rows, shared_data) {
    if (offset == 0) return false;
    if ((offset - rows) < 0) {
        shared_data.paging.offset = 0;
    } else {
        offset -= rows;
        shared_data.paging.offset = offset;
    }
    updateTable(shared_data);
    updatePaginationControls(shared_data);
}

function addHandler_checkBoxesChangeState(tg, shared_data) {
    $(tg).click(function(event) { 
        var lastBox = false;
        checkBoxHandler_changeState(event, this, shared_data);
    });
}

function addHandler_plusButtonAddsRow(tg, shared_data) {
    $(tg).click(function(event) {
        insertRowAfter(this, shared_data); 
    }); 
};

/**
 * Bind keyboard events to particular keystrokes; called after table initialization
 * 
 * FIXME: This should be modified to use BibEdit's hotkey system, which should itself
 *        be using jQuery's HotKey UI.
 * FIXME: Does this need to be called every updateTable?
 *
 * @param {Array} shared_data Passed to children
 */
function addHandler_keystrokesForInputBoxes(tg, shared_data) {
    var min_row = shared_data.paging.offset;
    var max_row = shared_data.paging.rows - 1;
    /** 
     * Put a row's data onto a holding stack.
     * 
     * @param {Input} box The input element in which this method was called.
     * @param {Array} shared_data The global state object. */
    function copyRowToCutBuffer(box, shared_data) { shared_data.row_cut = shared_data.authors[getRowNumber(box)]; }
    /** 
     * Remove a row from the displayed table and put its data onto a holding stack.
     * 
     * @param {Input} box The javascript input element associated with this cut.
     * @param {Array} shared_data The global state object. */
    function cutRowAndUpdateTable(box, shared_data) {
        var row = getRowNumber(box);
        var target_class = box.classList[0];
        copyRowToCutBuffer(box, shared_data);
        shared_data.authors.splice(row, 1);
        updateTable(shared_data);   // FIXME: use dom deletion by row instead
        if (row == shared_data.authors.length) {
            target = getRowSelector(row-1) +' .'+target_class;
            $(target).focus();
        } else { 
            $(getRowSelector(row)+' .'+target_class).focus(); 
        }
    }
    /** 
     * Insert a row from the holding stack onto the displayed table.
     * 
     * @param {Input} box The input element associated with this paste.
     * @param {Array} shared_data The global state object. */
    function pasteBelowAndUpdateTable(box, shared_data) {
        var target_id = box.getAttribute('id');
        var row = getRowNumber(box) + 1;
        var cut = shared_data['row_cut'];
        if (cut == null) return;
        shared_data['authors'].splice(row, 0, cut);
        // FIXME: use dom insertion by row instead (and call pagination cutoff function)
        updateTable(shared_data);
        $('#'+target_id).focus(); 
    }
    function moveByTG(tg, direction, box) {
        var starting = getRowNumber(box);
        var finishing = starting;
        if (direction == 'up') {
            if (starting === min_row) return;
            finishing -= 1;
        } else {
            if (starting === max_row) return;
            finishing += 1;
        }
        $(box).blur();
        $(getRowSelector(finishing)+' '+tg).focus()
        return;
    }

    $(tg).each(function (idx, element) {
        $(element).bind('keydown', 'alt+ctrl+x', function(event) {cutRowAndUpdateTable(this, shared_data); return false;} );
        $(element).bind('keydown', 'alt+ctrl+c', function(event) {copyRowToCutBuffer(this, shared_data); return false;} );
        $(element).bind('keydown', 'alt+ctrl+v', function(event) {pasteBelowAndUpdateTable(this, shared_data); return false;} );
        $(element).bind('keydown', 'alt+ctrl+n', function(event) {insertRowAfter(this, shared_data); return false;} );
        $(element).bind('keydown', 'alt+ctrl+l', function(event) { $(window).resize(); return false; } );
        if ($(element).hasClass('author_box')) {
            $(element).bind('keydown', 'alt+ctrl+down',  function(event) {moveByTG('.author_box', 'down', this); return false;});
            $(element).bind('keydown', 'alt+ctrl+up',    function(event) {moveByTG('.author_box', 'up',   this); return false;});
            $(element).bind('keydown', 'shift+tab', function(event) {moveByTG('.affil_box', 'up', this); return false;});
        } else if ($(element).hasClass('affil_box')) { 
            $(element).bind( 'keydown', 'alt+ctrl+down',  function(event) {moveByTG('.affil_box', 'down', this); return false;});
            $(element).bind( 'keydown', 'alt+ctrl+up',    function(event) {moveByTG('.affil_box', 'up',   this); return false;});
            $(element).bind( 'keydown', 'tab',       function(event) {moveByTG('.author_box', 'down', this); return false;});
        }
    });
}

/**
 * Decorate entry fields with calls to jQuery's AutoComplete UI.
 *
 * FIXME: users have requested that each item between ; and ; autocomplete, not just the last on, see
 *        also inputbox.getSelectionStart() and inputbox.getSelectionEnd(), http://javascript.nwbox.com/cursor_position/
 * 
 * @param {Array} shared_data
 */
function addHandler_autocompleteAffiliations(tg, shared_data) {
    function ultimate(s) {
        /* gets the last bit of text in semicolon-separated list */
        return jQuery.trim(s.slice(s.lastIndexOf(';')+1));
    }
    function penultimate(s) {
        /* gets everything up to last semicolon in semicolon-separated list */
        return jQuery.trim(s.substring(0, s.lastIndexOf(';')));
    }
    function add_selection_to(selection, to) {
        var to_str = penultimate(to.value);
        var new_value = jQuery.trim(to_str);
        if (new_value == '') new_value = selection;
        else new_value += '; ' + selection;
        $(to).val(new_value);
        return false;
    }
    $(tg).bind( "keydown", function( event) {
                        // don't navigate away from the field on tab when selecting an item
                        if ( event.keyCode === $.ui.keyCode.TAB && $(this).data("autocomplete").menu.active) {
                            event.preventDefault();
                        }
                   })
                   .autocomplete({
                       source: function( request, response ) {
                            $.getJSON("/kb/export",
                                      { kbname: 'InstitutionsCollection', format: 'jquery', term: ultimate(request.term) },
                                      response);
                       },
                       focus: function(event, ui) {
                           // focus happens when we use the mouse (cf. select)
                           // because we send focus, input box blur handler is implicitly called
                           add_selection_to(ui.item.value, this);
                           return false;
                       },
                       search: function() {
                           // custom minLength that knows to only use last item after semicolon
                           var term = ultimate(this.value);
                           if (term.length < 3) {
                               return false;
                           }
                       },
                       select: function(event, ui) {
                           // select happens when we use the keyboard (cf. focus)
                           // we add extra semicolon so we can keep typing and autocompleting
                           // because we keyboard, focus stays in box, so we call blur handler explicitly
                           add_selection_to(ui.item.value+'; ', this);
                           var returnto = this.id;
                           $(this).change();          // calls updateTable; DOM element 'this' ceases to exist
                           $('#'+returnto).focus();   // so we get back to the value we want by id instead
                           return false;
                       },
                       close: function(event, ui) {
                           $(this).focus();
                           return false;
                       },
                   });
}

/**
 * Calculate the (HTML) contents of the table header.
 * @param {Array} shared_data The dictionary of shared state; uses 'affiliations'
 */
function generateTableHeader(tg, inst_list) {
    var i, label, sliced;
    $('#NonTableHeaders').html(''); // DEBUG
    $(tg).html('<div class="header allrows header_container"><div class="rownum header">#</div><div class="author_box author_head header">author</div><div class="affil_box affil_head header">affiliations</div><div class="add_row_img_head header"><img src="/img/add-small.png" class="add_row_img" /></div></div>');
    for (i = 0; i < inst_list.length; i++) {
        label = inst_list[i];
        sliced = '';
        if (label.length > 10) {                 // XXX: 10 is magic number
            sliced = label.slice(0,7)+'...';
        } else {
            sliced = label;
        } 
        label = (i+1).toString() + '. ' + label;
        sliced = '<span class="column_no">'+(i+1).toString() + '</span><br />' + sliced;
        $('.header_container').append('<div class="column_content col'+i+' column_label header"><a title="'+label+' - Click to hide." href="#" class="hide_link" name="'+i+'">'+sliced+'</a></div>');
    }
}

function applyToRows(fn, start_at, stop_at) {
    var row;
    for (row = start_at; row < stop_at; row++) {
        fn(row);
    }
}

/**
 * Dynamically create the table cells necessary to hold up to shared_data.paging.rows of data
 */
function generateTableBody(tg, shared_data) {
    var authors, maxrows, offset, stop;
    authors = shared_data['authors'];
    maxrows = shared_data['paging'].rows*1;
    stop = maxrows;
    offset = shared_data['paging'].offset*1;       // caution: numbering starts at 0
    if ((offset + maxrows) < authors.length) {
        stop = offset + maxrows;
    } else {
        stop = authors.length;
    }
    function fn(row) {
        $('\n<tr id="table_row_'+row+'" class="row row'+row+'" row="'+row+'"></tr>\n').appendTo(tg);
        setRow(row, shared_data);
    }
    $(tg).html('');
    applyToRows(fn, offset, stop);
}

/**
 * Emit a single row of a dynamically generated table.
 * 
 * @param {Integer} row The row index (0-based)
 * @param {Array} auth_affils [author_name, affiliation1, affiliation2, ...]
 * @param {Array} institutions The list of represented affiliations
 * @return {String} The HTML to be emitted to the browser
 */
function generateRowContents(row, auth_affils, institutions) {

    var my_id = getID(); // used to get globally unique name not connected to row number
    var str = '';
    // preamble
    str += '<td class="rownum bodyrow"><span class="rownuminner">'+ (row+1) +'</span></td>';

    // author name
    str += '<td class="author_box_td"><input type="text" class="author_box" id="author_'+my_id+'" name="autho'+row+'" value="'+auth_affils[0]+'"';
    if (row === 0) {
        str += ' title="100a: first author"';
    } else {
        str += ' title="700a: additional author"';
    }
    str += '></td>'

        // affiliations
        str += '<td class=affil_box_td row='+row+'><input type="text" class="affil_box" id="affils_'+my_id+'" name="insts'+row+'" value="';
    str += filter_ArrayToSemicolonString(auth_affils.slice(1)) + '"';
    if (row == 0) {
        str += ' title="100u: first author\'s affiliations"';
    } else {
        str += ' title="700u: additional author\'s affiliations"';
    }
    str += '></td><td class=add_row_img_container><img src="/img/add-small.png" row='+row+' title="Insert new row below this one" class=add_row_img /></td>';

    // checkboxes
    for (var col = 0; col < institutions.length; col++) {
        var inst_name = jQuery.trim(institutions[col]);
        var name = inst_name+'_'+my_id;
        str += '<td class="bodyrow column_content col'+col+'" col='+col+'><input type="checkbox" title="'+institutions[col];
        str +=          '" class="check_col'+col+'" col='+col+' id=checkbox_'+my_id+'_'+col+' value="'+name+'"';
        for (var place = 1; place < auth_affils.length; place++) {
            if (auth_affils[place] == inst_name) {
                str += ' checked';
                if (!shared_data['affilcounts'][col]) {
                    shared_data['affilcounts'][col] = 1;
                } else {
                    shared_data['affilcounts'][col] += 1;
                }
            }
        }
        str += ' /></td>';
    }

    return str;
}

/** 
 * "fold" a column in the table.
 *
 * FIXME: This is probably broken.
 * 
 * @param {int} col The column number to fold
 * @param {String} title The mouseover floating text for the element
 */
function foldColumn(col, title) {
    $('.col'+col).before('<td title="'+title+'" class="empty'+col+' empty" style="width: 2px; border-style: hidden solid hidden solid;"><span class="column_no"></span></td>');
    $('.empty'+col).click( 
        function() { 
            $('.empty'+col).remove();
            $('.col'+col).show();
            shared_data['folded'].splice($.inArray(col, shared_data['folded']));
            return false;
        });
    $('.col'+col).hide();
    return false;
}

/**
 * Search the affiliations for an author looking for this checkbox.
 *
 * lastBox is captured from our outer context (addHandler...)
 */
function checkBoxHandler_changeState(event, thisBox, shared_data) {
    function cdr(arr) {
        return arr.slice(1);
    }

    function set_box(box, state) {
        var row = getRowNumber(box);
        var rowselector = getRowSelector(row);
        var col = box.getAttribute('col') * 1;
        var institution = box.title;
        var auth_affils = shared_data['authors'][row];
        var affils_idx = $.inArray(institution, cdr(auth_affils)) + 1;
        box.checked = state
            if (box.checked) {
                // we want it
                if (! affils_idx) {
                    // if it's not here, add it
                    auth_affils.push(institution);
                    $(rowselector+' .affil_box').val(filter_ArrayToSemicolonString(cdr(auth_affils)));
                    shared_data['affilcounts'][col] += 1;
                } 
            } else {
                // we don't want it
                if (affils_idx) {
                    // it's here, though, so remove it
                    auth_affils.splice(affils_idx, 1);
                    $(rowselector+' .affil_box').val(filter_ArrayToSemicolonString(cdr(auth_affils)));
                    shared_data['affilcounts'][col] -= 1;
                } 
            }
    }

    // FIXME: when iterating to do a shiftClick, skip folded columns
    // FIXME: there must be a way to make this use fewer lines of code, mustn't there?
    if (event.shiftKey && lastBox) {   // shift click in effect, and
        var row = getRowNumber(thisBox);
        var col = thisBox.getAttribute('col') * 1;
        var lastRow = getRowNumber(lastBox);
        var lastCol = lastBox.getAttribute('col') * 1;
        var startRow = Math.min(row, lastRow);
        var endRow = Math.max(row, lastRow);
        var startCol = Math.min(col, lastCol);
        var endCol = Math.max(col, lastCol);
        for (var i = startRow; i <= endRow; i++) {
            $(getRowSelector(i)).find('input[type=checkbox]').each(function (j, box) {
                if ((j < startCol) || (j > endCol)) return;
                set_box(box, lastBox.checked);
            });
        }
        lastBox = false;
    }
    else {                             // unshifted (ie, normal) click
        lastBox = thisBox;
        set_box(thisBox, thisBox.checked);
    }
    // if checkboxing has made any affiliation count go to zero, redraw 
    if (jQuery.inArray(0, shared_data['affilcounts']) > -1) updateTable(shared_data); 
}

/**
 * add a class on focus, remove it on blur
 */
function addHandler_currentRowHilight(tg, shared_data) {
    // make every text entry box hilight its row
    $(tg).focus(function() { 
        shared_data.crs = $(this).val(); 
        $(this.parentNode.parentNode).addClass('current_row') 
    });
    $(tg).blur(function() { 
        if ($(this).val() != shared_data.crs) {
            $(this).change(); 
            $(this).resize();
        }
        $(this.parentNode.parentNode).removeClass('current_row') 
    });
}

/**
 * Scrub user input in the author box, then sync it to shared_data.
 */
function addHandler_scrubAndSynchToAuthors(tg, shared_data) {
    $(tg).change(function() { 
        var row = getRowNumber(this);
        var scrubbed = jQuery.trim(filter_escapeHTML(this.value));
        shared_data['authors'][row][0] = scrubbed;
        this.value = scrubbed;
    });
}

/**
 * Sync the affiliations box to shared_data, then sync shared_data to the checkboxes
 */
function addHandler_semicolonSepBoxToAffiliations(tg, shared_data) {
  $(tg).change(function() {
      var addColumn_flag, authorName, row, newRow, oldRow, 
      row = getRowNumber(this);
      row_selector = getRowSelector(row);
      //oldRow = shared_data.authors[row];
      //authorName = oldRow[0];
      authorName = shared_data.authors[row][0];
      if (authorName === '') {  
        // TODO: revisit this; a more discrete warning would be nicer, e.g.:
        // add class decorator to this row's author if it's empty
        // doesn't work because we completely redraw the table periodically
        //$(getRowSelector(row).concat(' > .author_box_td').concat(' > .author_box')).addClass('MalformedData')
        alert('Row ' + row + ' has affiliations with no author name; this is not allowed. Please separate multiple affiliations for one author by using semicolons, and enter them in the same box.')
      } else {
        // remove class decorator from this row's author if it's empty
        // doesn't work because we completely redraw the table periodically
        //$(getRowSelector(row).concat(' > .author_box_td').concat(' > .author_box')).removeClass('MalformedData')
      }
      newRow = filter_SemicolonStringToArray(this.value);
      newRow.unshift(authorName);
      //addColumn_flag = false;
      // filter newRow: check for integers to substitute or new affiliations to add on
      for (var i = 1; i < newRow.length; i++) {
          var item = newRow[i];
          var item_as_colno = parseInt(item);
          if ((item_as_colno == item-0) &&                             // it is:  small int w/ no junk chars
              (item_as_colno > 0) &&                                   // it has: value 1 or more
              (item_as_colno <= shared_data['affiliations'].length)) { // it has: value <= max + 1
              /* column number given */
              newRow[i] = shared_data['affiliations'][item-1];
              shared_data['affilcounts'][item-1] += 1; 
          } else {                                                     // it is: an affiliation name
              /* unseen, meaningful values get added as new columns 
                 FIXME: unseen meaningful values should fire an institution addition RT Ticket */
              if ((jQuery.inArray(item, shared_data.affiliations) === -1) && (item != '')) {
                shared_data['affiliations'].push(item);
                shared_data['affilcounts'].push(1);
                //addColumn_flag = true;
              }
          }
      }
      shared_data['authors'][row] = newRow;
      updateTable(shared_data); // XXX: we should be able to add columns directly
      /*if (addColumn_flag) { 
          updateTable(shared_data); // XXX: we should be able to add columns directly
      } else { 
          // subtract off the old row's affiliation counts, since we are about to make a new one
          for (var i = 0; i < shared_data.affiliations.length; i++) {
              if (oldRow.indexOf(shared_data.affiliations[i]) != -1) shared_data.affilcounts[i]--;
              if (shared_data.affilcounts[i] == 0) addColumn_flag = true;
          }
          if (addColumn_flag) return updateTable(shared_data);
          setRow(row, shared_data);
      } */
    });
    return false;
}

/** 
 * Convert a semicolon-separated-value string into a list.
 * Escape content and remove empty strings.
 *
 * @param {String} value A string of the form 'cat; dog; tiger'
 * @returns {Array} An array like ['cat', 'dog', 'tiger']
 */
function filter_SemicolonStringToArray(value) {
  return jQuery.map(value.split(';'), function(v, junk) {
      s = jQuery.trim(v);
      if (s != '') return filter_escapeHTML(s);   /* sanitize and return */
  });
}

/**
 * Convert a list into a semicolon-separated-value string.
 * Remove empty strings and whitespace-only.  Collapse multiple spaces to one.
 * 
 * @param {Array} list A 1d arry of strings, e.g., ['', 'cat', 'dog','    ', 'tiger']
 * @returns {String} A string of the form 'cat;dog;tiger'
 */
function filter_ArrayToSemicolonString(list) {
    list = jQuery.map(list, function(v, i) { v = jQuery.trim(v); if (v == '') return null; return v; }); // trim and remove blanks
    retval = list.join(';');
    if (retval != '') { retval += ';' };
    retval = retval.replace(/\s+/g, ' ').replace(/; ;/g, ';').replace(/;+/g, ';');
    return retval;
}

/**
 * Replace special characters '&', '<' and '>' with HTML-safe sequences.
 * This functions is called on content before displaying it.
 */
function filter_escapeHTML(value){
  value = value.replace(/&/g, '&amp;'); // Must be done first!
  value = value.replace(/</g, '&lt;');
  value = value.replace(/>/g, '&gt;');
  return value;
}

