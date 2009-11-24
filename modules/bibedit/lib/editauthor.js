/**********************
 * See: http://jsdoc.sourceforge.net/
 **********************/

//TODO ITEMS: 
// * MORE/BETTER/MORE CONSISTENT JSDOC.
// * Continue integration with Invenio (output to MARCXML and BibUpload)
// * REFACTOR TO USE jQUERY UTILITIES, map, apply AND SELECTORS BETTER.  (TOO MANY FOR LOOPS)
// * Integration with BibKnowledge

/** 
 * NB: Initialization values for debug purposes only.
 */
shared_data = {
  'affiliations': [], 
  'authors':      [ [], ], 
  'folded':       [],
};

/** 
 * main: this target fires as soon as the DOM is ready, which may be before
 *       the page download is complete.  Everything else is driven from here.
 */
$(document).ready(
  function() {
    // environment initialization/table building
    initTable(shared_data);

    // startup behaviors
    $('#affils_0').focus()

    // for DEBUG only; makes working js parse obvious
    $('table').css("bgcolor", "#91ff91");
  }
);

/**
 * Throw up a loading message and call updateTable*
 * 
 * @param {Array} shared_data Passed to children
 */
function initTable(shared_data) {
    $('#TableHeaders').html('<p id="loading_msg">Loading; please wait...</p>');
    $('#TableContents').html('<p id="loading_msg">Loading; please wait...</p>');
    updateTable(shared_data);
}

/** 
 * "fold" a column in the table.
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
        });
    $('.col'+col).hide();
}

/**
 * Create the HTML representation of a table representing shared_data, assign
 * event handlers, and maintain folding status.
 * 
 * @param {Array} shared_data The dictionary of shared state
 */
function updateTable(shared_data) {

    $('#TableHeaders').html( generateTableHeader(shared_data['affiliations']) );
    $('a.hide_link').click( 
        function() { 
            shared_data['folded'].push(this.name); 
            foldColumn(this.name, this.title.replace('hide', 'expand'));
        });

    $('#TableContents').html( generateTableBody(shared_data) );

    addCheckBoxHandlers(shared_data);
    addTextBoxHandlers(shared_data);

    for (var i in shared_data['folded']) {
        if (shared_data['folded'][i]  != null) {
            foldColumn(shared_data['folded'][i], "Click to expand.");
        }
    }
}

/**
 * Calculate the (HTML) contents of the table header.
 * 
 * @param {Array} shared_data The dictionary of shared state; uses 'affiliations'
 * @returns {String} The computed HTML of the table header line
 */
function generateTableHeader(inst_list) {

    var computed_text = '<tr><th>#</th><th title="Author\'s name, one per line.">name</th>';
    computed_text += '<th title="Institutional affiliations.  Semicolon-separated list.">affiliation</th>';

    for (var i = 0; i < inst_list.length; i++) {
        var label = inst_list[i];
        var sliced = '';
        if (label.length > 10) {
            sliced = label.slice(0,7)+'...';
        } else {
            sliced = label;
            for (var j = 10 - label.length; j > 0; j--) {
                sliced += '&nbsp;';
            }
        }
        computed_text += '<th class="col'+i+'"><a title="'+label+' - Click to hide." href="#" class="hide_link" name="'+i+'">'+sliced+'</a></th>';
    }
    computed_text += '</tr>\n';
    return computed_text;
}

/**
 * Dynamically create the table cells necessary to hold everything
 *
 * @param {Array} author_list A list of author_institution pairs
 * @param {Array} institution_list A list of institutions for checkbox columns
 */
function generateTableBody(shared_data) {
    var computed_body = '';
    for (var row = 0; row < shared_data['authors'].length; row++) {
        computed_body += generateTableRow(row, shared_data['authors'][row], shared_data['affiliations']);
    }
    return computed_body;
}

/**
 * Emit a single row a dynamically generated table.
 * 
 * @param {Integer} row The row index (0-based)
 * @param {Array} auth_affils [author_name, affiliation1, ...]
 * @param {Array} institutions The list of possible affiliations
 * @return {String} The HTML to be emitted to the browser
 */
function generateTableRow(row, auth_affils, institutions) {

    var str = '';
    // preamble
    str += '\n<tr id="table_row_'+row+'" class="row'+row+'"><td class="rownum">'+ (row+1) +'</td>';
        
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
    str += auth_affils.slice(1).join(';') + '"';
    if (row == 0) {
        str += ' title="100u: first author\'s affiliations"';
    } else {
        str += ' title="700u: additional author\'s affiliations"';
    }
    str += '></td>';

    // checkboxes
    for (var i = 0; i < institutions.length; i++) {
        var inst_name = institutions[i];
        var name_row = inst_name+'_'+row;
        str += '<td><input type="checkbox" title="'+institutions[i];
        str +=           '" class="col'+i+'" id="checkbox_'+row+'_'+i+'" value="'+name_row+'"';
        for (var place = 1; place < auth_affils.length; place++) {
            if (auth_affils[place] == inst_name) {
                str += ' checked';
            }
        }
        str += '></td>';
    }
    str += '</tr>\n';
    
    return str;
}

/**
 * Adds change handlers to checkboxes so table row state gets toggled correctly
 *
 * @param {Object} shared_data The global state object which the handlers mutate
 */
function addCheckBoxHandlers(shared_data) {
  $('input[type="checkbox"]').click( function() { addCheckBoxHandlers_changeHandler(shared_data, this) } );
}

/**
 * Search the affiliations for an author looking for this checkbox.
 */
function addCheckBoxHandlers_changeHandler(shared_data, me) {
  var myrow = me.value.substring(me.value.lastIndexOf('_')+1);
  var myaffils = shared_data['authors'][myrow].slice(1);
  var myname = me.value.slice(0, me.value.indexOf('_'));
  var cb_loc = $.inArray(myname, myaffils);

  if ((me.checked == true) && (cb_loc == -1)) {
      // we want it, but it's not here
      shared_data['authors'][myrow].push(myname);
      addCheckBoxHandlers_inputSync(shared_data, myrow, myname);
  } else if ((me.checked == true) && (cb_loc != -1)) {
      // we want it, but it's already here
      return;
  } else if ((me.checked == false) && (cb_loc == -1)) {
      // we don't want it, and it's not here
      return;
  } else if ((me.checked == false) && (cb_loc != -1)) {
      // we don't want it, and it's here
      cb_loc += 1; // XXX: index taken from slice, but used in a splice
      shared_data['authors'][myrow].splice(cb_loc, 1);
      addCheckBoxHandlers_inputSync(shared_data, myrow, myname);
  }
}

/**
 *Sync the contents of shared_data into this row's affils box
 */
function addCheckBoxHandlers_inputSync(shared_data, myrow, myname) {
  $('#affils_'+myrow).attr("value", shared_data['authors'][myrow].slice(1).join(';'));
}

/**
 * Adds blur handlers to text input boxes so checkbox state gets toggled correctly
 *
 * @param {Object} shared_data The global state object which the handlers mutate
 */
function addTextBoxHandlers(shared_data) {
  $('.author_box').blur( function() { addAuthBoxHandlers_blurHandler(shared_data, this) } );
  $('.affil_box').blur( function() { addAffilBoxHandlers_blurHandler(shared_data, this) } );
}

/**
 * Scrub user input in the author box, then sync it to shared_data and redraw.
 */
function addAuthBoxHandlers_blurHandler(shared_data, me) {
  var myrow = me.id.substring(me.id.lastIndexOf('_')+1);
  var myname = escapeHTML(me.value);
  shared_data['authors'][myrow][0] = myname;
  updateTable(shared_data);
}

/**
 * Sync the affiliations box to shared_data, then sync shared_data to the checkboxes
 */
function addAffilBoxHandlers_blurHandler(shared_data, me) {
  var myrow = me.id.substring(me.id.lastIndexOf('_')+1);
  var myname = shared_data['authors'][myrow][0];
  var newRow = $.map(me.value.split(';'), function(s, i) {
      s = $.trim(s);
      if (s == '') return null;   /* drop empty strings */
      else return escapeHTML(s);  /* otherwise, sanitize & return */
  });
  for (var item in newRow) {
      var datum = newRow[item];
      if ($.inArray(datum, shared_data['affiliations']) == -1) {
        shared_data['affiliations'].push(datum);
      }
  }
  me.value = newRow.join(';');
  newRow.unshift(myname);
  shared_data['authors'][myrow] = newRow;
  updateTable(shared_data);
}

/**
 * Replace special characters '&', '<' and '>' with HTML-safe sequences.
 * This functions is called on content before displaying it.
 */
function escapeHTML(value){
  value = value.replace(/&/g, '&amp;'); // Must be done first!
  value = value.replace(/</g, '&lt;');
  value = value.replace(/>/g, '&gt;');
  return value;
}
