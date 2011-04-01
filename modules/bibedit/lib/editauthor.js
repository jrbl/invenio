/**********************
 * See: http://jsdoc.sourceforge.net/
 **********************/

// FIXME: take advantage of jQuery 1.4+; use focusOut instead of blur where it makes sense (etc)

/** 
 * NB: Initialization values for debug purposes only.
 */
shared_data = {
  'authors':      [ [], ],        // set of all [author, affiliation1, affiliation2 ...]
  'affiliations': [],             // list of institutions present in this data
  'paging':       {},             // dictionary for keeping track of pagination of large lists
  'valid_affils': [],             // list of possible institutional affiliations // FIXME: Remove?
  'folded':       [],             // which columns are currently hidden
  'row_cut':      [],             // the row recently removed from the data set with 'cut'
  'headline':     {},             // recid, paper title
};

/** 
 * main: this target fires as soon as the DOM is ready, which may be before
 *       the page download is complete.  Everything else is driven from here.
 */
$(document).ready(
  function() {
    var data = shared_data;

    // calculate whether to show the pagination widget
    data.paging.pages = Math.ceil(data.authors.length / data.paging.rows);

    // startup behaviors
    $('<link rel="stylesheet" type="text/css" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/themes/redmond/jquery-ui.css" />').appendTo("head");
    $.ajax({ url: "/img/editauthor.css", success: function(results) {
        $("<style></style>").appendTo("head").html(results);
    }}); 
    $('#submit_button').css('display', 'inline'); // jQuery parses so make the button live

    // keep enter key from submitting the page form
    $(window).keydown(function(event){ if(event.keyCode == 13) { event.preventDefault(); return false; } });

    // set popup title
    $('#asm_form').attr('title', data.headline.recid + ': ' + data.headline.title);

    // add the pagination widget (only displays if it's needed)
    updatePaginationControls(data);

    // Tell the user the tables are loading, then go build them
    $('#TableHeaders').html('<p id="loading_msg">Loading; please wait...</p>');
    $('#TableContents').html('<p id="loading_msg">Loading; please wait...</p>');
    updateTable(data);

    // create popup and display it
    $('#asm_form').dialog({
        autoOpen: true,
        height: 550,
        width: 1020,
        modal: true,
        position: "center",
    });

    $('#affils_0').focus();
  }
);

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

/**
 * Create the HTML representation of a table representing shared_data, assign
 * event handlers, and maintain folding status.
 * 
 * @param {Array} shared_data The dictionary of shared state
 */
function updateTable(shared_data) {

    // generate table header & body
    $('#TableHeaders').html(  generateTableHeader(shared_data['affiliations']) );
    $('#TableContents').html( generateTableBody(shared_data) );

    // add column folding click handlers
    $('a.hide_link').click(       // FIXME: id selector faster?  does it matter?
        function() { 
            shared_data['folded'].push(this.name); 
            foldColumn(this.name, this.title.replace('hide', 'expand'));
        });

    // add text box handlers (table updates, keystrokes and autocompletes)
    addTextBoxHandlers(shared_data);
    addKeyStrokes(shared_data); 
    addAutocompletes(shared_data);

    // add checkbox handlers
    $('input[type="checkbox"]').click( // FIXME: id selector faster?  does it matter?
        function(event) { 
            var lastBox = false;
            checkBoxHandler_changeState(event, this, shared_data);
        });

    // fold the columns previously checked
    for (var i in shared_data['folded']) {
        if (shared_data['folded'][i]  != null) {
            foldColumn(shared_data['folded'][i], "Click to expand.");
        }
    }
    return false;
}

/**
 * Bind keyboard events to particular keystrokes; called after table initialization
 * 
 * FIXME: This should be modified to use BibEdit's hotkey system, which should itself
 *        be using jQuery's HotKey UI.
 * FIXME: Does this need to be called every updateTable?
 *
 * @param {Array} shared_data Passed to children
 */
function addKeyStrokes(shared_data) {
    var min_row = shared_data.paging.offset;
    var max_row = shared_data.paging.rows - 1;
    /** 
     * Put a row's data onto a holding stack.
     * 
     * @param {Input} box The input element in which this method was called.
     * @param {Array} shared_data The global state object. */
    function copyRowAndUpdateTable(box, shared_data) {
        var row = box.parentNode.parentNode.getAttribute('row') * 1;
        shared_data['row_cut'] = shared_data['authors'][row];
    }
    /** 
     * Remove a row from the displayed table and put its data onto a holding stack.
     * 
     * @param {Input} box The javascript input element associated with this cut.
     * @param {Array} shared_data The global state object. */
    function cutRowAndUpdateTable(box, shared_data) {
        var target_id = box.getAttribute('id');
        var row = box.parentNode.parentNode.getAttribute('row') * 1;
        copyRowAndUpdateTable(box, shared_data);
        shared_data['authors'].splice(row, 1);
        updateTable(shared_data);
        if (row == shared_data['authors'].length) {
            target = '#' + target_id.slice(0, target_id.lastIndexOf('_')+1) + (row - 1);
            $(target).focus();
        } else { $('#'+target_id).focus(); }
    }
    /** 
     * Insert a row from the holding stack onto the displayed table.
     * 
     * @param {Input} box The input element associated with this paste.
     * @param {Array} shared_data The global state object. */
    function pasteBelowAndUpdateTable(box, shared_data) {
        var target_id = box.getAttribute('id');
        var row = box.parentNode.parentNode.getAttribute('row') * 1 + 1;
        var cut = shared_data['row_cut'];
        if (cut == null) return;
        shared_data['authors'].splice(row, 0, cut);
        updateTable(shared_data);
        $('#'+target_id).focus();
    }
    /**
     * Move to the next author box.
     *
     * @param {String} direction 'up' or 'down'
     * @param {Array} shared_data The global state object. */
    function moveByAuthor(direction, box) {
        var starting = box.parentNode.parentNode.getAttribute('row') * 1;
        if (direction == 'up') {
            if (starting == min_row) return;
            $('#author_'+(starting - 1)).focus();
        } else {
            if (starting == max_row) return;
            $('#author_'+(starting + 1)).focus();
        }
        return;
    }
    /**
     * Move to the next affiliations box.
     *
     * @param {String} direction 'up' or 'down'
     * @param {Array} shared_data The global state object. */
    function moveByAffils(direction, box) {
        var starting = box.parentNode.parentNode.getAttribute('row') * 1;
        if (direction == 'up') {
            if (starting == min_row) return;
            $('#affils_'+(starting - 1)).focus();
        } else {
            if (starting == max_row) return;
            $('#affils_'+(starting + 1)).focus();
        }
        return;
    }

    $('input').bind('keydown', 'alt+ctrl+x', function(event) {cutRowAndUpdateTable(this, shared_data); return false;} );
    $('input').bind('keydown', 'alt+ctrl+c', function(event) {copyRowAndUpdateTable(this, shared_data); return false;} );
    $('input').bind('keydown', 'alt+ctrl+v', function(event) {pasteBelowAndUpdateTable(this, shared_data); return false;} );
    $('.author_box').bind('keydown', 'alt+down',  function(event) {moveByAuthor('down', this); return false;});
    $('.affil_box').bind( 'keydown', 'alt+down',  function(event) {moveByAffils('down', this); return false;});
    $('.author_box').bind('keydown', 'alt+up',    function(event) {moveByAuthor('up',   this); return false;});
    $('.affil_box').bind( 'keydown', 'alt+up',    function(event) {moveByAffils('up',   this); return false;});
    $('.affil_box').bind( 'keydown', 'tab',       function(event) {moveByAuthor('down', this); return false;});
    $('.author_box').bind('keydown', 'shift+tab', function(event) {moveByAffils('up', this); return false;});
}

/**
 * Decorate entry fields with calls to jQuery's AutoComplete UI.
 * 
 * @param {Array} shared_data
 */
function addAutocompletes(shared_data) {
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
    /* FIXME: Use ID selector, not class selector ? */
    $(".affil_box").bind( "keydown", function( event) {
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
                           return add_selection_to(ui.item.value, this);
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
                           return add_selection_to(ui.item.value+'; ', this);
                       },
                       close: function(event, ui) {
                           this.focus();
                           return false;
                       },
                   });
}

/**
 * Calculate the (HTML) contents of the table header.
 * 
 * @param {Array} shared_data The dictionary of shared state; uses 'affiliations'
 * @returns {String} The computed HTML of the table header line
 */
function generateTableHeader(inst_list) {

    var computed_text = '<tr class="allrows"><th class="rownum">#</th><th class="author_box author_head" title="Author\'s name, one per line.">name</th>';
    computed_text += '<th class="affil_box affil_head" title="Institutional affiliations.  Semicolon-separated list.">affiliation</th>';

    for (var i = 0; i < inst_list.length; i++) {
        var label = inst_list[i];
        var sliced = '';
        if (label.length > 10) {                 // XXX: 10 is magic number
            sliced = label.slice(0,7)+'...';
        } else {
            sliced = label;
        } 
        label = (i+1).toString() + '. ' + label;
        sliced = '<span class="column_no">'+(i+1).toString() + '</span><br />' + sliced;
        computed_text += '<th class="column_content col'+i+' column_label">'
        computed_text += '<a title="'+label+' - Click to hide." href="#" class="hide_link" name="'+i+'">'+sliced+'</a></th>';
    }
    computed_text += '</tr>\n';
    return computed_text;
}

/**
 * Dynamically create the table cells necessary to hold up to shared_data.paging.rows of data
 */
function generateTableBody(shared_data) {
    var offset = shared_data['paging'].offset*1;       // caution: numbering starts at 0
    var maxrows = shared_data['paging'].rows*1;
    var authors = shared_data['authors'];
    var stop_at;
    if ((offset + maxrows) < (authors.length*1)) { // we have another page of results at least
        stop_at = offset + maxrows;
    } else {                                                  // this is the last page of results
        stop_at = authors.length;
    }

    var computed_body = '';
    for (var row = offset; row < stop_at; row++) {
        computed_body += generateTableRow(row, authors[row], shared_data['affiliations']);
    }
    return computed_body;
}

/**
 * Emit a single row of a dynamically generated table.
 * 
 * @param {Integer} row The row index (0-based)
 * @param {Array} auth_affils [author_name, affiliation1, affiliation2, ...]
 * @param {Array} institutions The list of represented affiliations
 * @return {String} The HTML to be emitted to the browser
 */
function generateTableRow(row, auth_affils, institutions) {

    var str = '';
    // preamble
    str += '\n<tr id="table_row_'+row+'" class="row row'+row+'" row="'+row+'"><td class="rownum">'+ (row+1) +'</td>';
        
    // author name
    str += '<td><input type="text" class="author_box" id="author_'+row+'" name="autho'+row+'" value="'+auth_affils[0]+'"';
    if (row == 0) {
        str += ' title="100a: first author"';
    } else {
        str += ' title="700a: additional author"';
    }
    str += '></td>'
            
    // affiliations
    str += '<td><input type="text" class="affil_box" id="affils_'+row+'" name="insts'+row+'" value="';
    str += filter_ArrayToSemicolonString(auth_affils.slice(1)) + '"';
    if (row == 0) {
        str += ' title="100u: first author\'s affiliations"';
    } else {
        str += ' title="700u: additional author\'s affiliations"';
    }
    str += '></td>';

    // checkboxes
    for (var col = 0; col < institutions.length; col++) {
        var inst_name = jQuery.trim(institutions[col]);
        var name_row = inst_name+'_'+row;
        str += '<td class="column_content"><input type="checkbox" title="'+institutions[col];
        str +=          '" class="col'+col+'" row='+row+' col='+col+' id="checkbox_'+row+'_'+col+'" value="'+name_row+'"';
        for (var place = 1; place < auth_affils.length; place++) {
            if (auth_affils[place] == inst_name) {
                str += ' checked';
            }
        }
        str += ' /></td>';
    }
    str += '</tr>\n';
    
    return str;
}

/** 
 * "fold" a column in the table.
 *
 * FIXME: this would be significantly faster with id selectors instead of class selectors.  Also with selector caching.
 *        Cf. http://net.tutsplus.com/tutorials/javascript-ajax/10-ways-to-instantly-increase-your-jquery-performance/
 * 
 * @param {int} col The column number to fold
 * @param {String} title The mouseover floating text for the element
 */
function foldColumn(col, title) {
    $('.col'+col).before('<td title="'+title+'" class="empty'+col+'" style="border-style: hidden solid hidden solid;"></td>');
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
 */
function checkBoxHandler_changeState(event, thisBox, shared_data) {
    // lastBox brought in from enclosing scope in updateTable
    function cdr(arr) {
        return arr.slice(1);
    }

    function set_box(box, state) {
        var row = box.getAttribute('row') * 1;
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
              $('#affils_'+row).val(filter_ArrayToSemicolonString(cdr(auth_affils)));
          } 
        } else {
          // we don't want it
          if (affils_idx) {
              // it's here, though, so remove it
              auth_affils.splice(affils_idx, 1);
              $('#affils_'+row).val(filter_ArrayToSemicolonString(cdr(auth_affils)));
          } 
        }
    }

    // FIXME: when iterating to do a shiftClick, skip folded columns
    // FIXME: there must be a way to make this use fewer lines of code, mustn't there?
    if (event.shiftKey && lastBox) {   // shift click in effect, and
        var row = thisBox.getAttribute('row') * 1;
        var col = thisBox.getAttribute('col') * 1;
        var lastRow = lastBox.getAttribute('row') * 1;
        var lastCol = lastBox.getAttribute('col') * 1;
        var startRow = Math.min(row, lastRow);
        var endRow = Math.max(row, lastRow);
        var startCol = Math.min(col, lastCol);
        var endCol = Math.max(col, lastCol);
        for (var i = startRow; i <= endRow; i++) {
            $('#table_row_'+i+' [type=checkbox]').each(function (j, box) {
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

}

/**
 * Adds blur handlers to text input boxes so checkbox state gets toggled correctly
 *
 * @param {Object} shared_data The global state object which the handlers mutate
 */
function addTextBoxHandlers(shared_data) {
  var size = shared_data.authors.length;
  function inner(ii) {
      $('#author_'+ii).change( function() { addAuthBoxHandlers_changeHandler(shared_data, ii, this.value) } );
      $('#affils_'+ii).change( function() { addAffilBoxHandlers_changeHandler(shared_data, ii, this.value) } );
  };
  for (var i = 0; i < size; i++) {
      inner(i);
  };
}

/**
 * Scrub user input in the author box, then sync it to shared_data and redraw.
 */
function addAuthBoxHandlers_changeHandler(shared_data, row, value) {
  shared_data['authors'][row][0] = filter_escapeHTML(value);
}

/**
 * Sync the affiliations box to shared_data, then sync shared_data to the checkboxes
 */
function addAffilBoxHandlers_changeHandler(shared_data, row, value) {
  var myname = shared_data['authors'][row][0];
  var newRow = filter_SemicolonStringToArray(value);
  for (var i = 0; i < newRow.length; i++) {
      var item = newRow[i];
      var item_as_colno = parseInt(item);
      if ((item_as_colno == item-0) &&                             // it is:  small int w/ no junk chars
          (item_as_colno > 0) &&                                   // it has: value 1 or more
          (item_as_colno <= shared_data['affiliations'].length)) { // it has: value <= max + 1
          /* column number given */
          newRow[i] = shared_data['affiliations'][item-1];
      } else {                                                     // it is: a normal affiliation
          /* unseen, meaningful values get added as new columns 
             FIXME: unseen meaningful values should fire an institution addition */
          if ((jQuery.inArray(item, shared_data['affiliations']) == -1) && (item != '')) {
            shared_data['affiliations'].push(item);
          }
      }
  }
  newRow.unshift(myname);
  shared_data['authors'][row] = newRow;
  updateTable(shared_data);
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
    list = jQuery.map(list, function(v, i) { v = jQuery.trim(v); if (v == '') return null; return v; });
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

