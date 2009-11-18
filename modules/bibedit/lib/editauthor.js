/**********************
 * See: http://jsdoc.sourceforge.net/
 **********************/

//TODO ITEMS: 
// * MORE/BETTER/MORE CONSISTENT JSDOC.
// * Dynamic columns: adding cols with box entries, hiding columns
// ** Make this prettier: use callbacks to insert dummy columns with borders which can be clicked to re-expand
// * Continue integration with Invenio (output to MARCXML and BibUpload)
// * REFACTOR TO USE jQUERY UTILITIES, map, apply AND SELECTORS BETTER.  (TOO MANY FOR LOOPS)
// * Integration with BibKnowledge

/** 
 * NB: Initialization values for debug purposes only.
 */
shared_data = {
  'affiliations': ["CERN", "DESY", "SLAC", "Fermilab", "SUNY", "Brookhaven", "NASA Jet Propulsion Laboratory"],
  'authors': [ ["Tibor Simko", "CERN"], ["Anette Holtkamp", "CERN", "DESY"], 
               ["Joe Blaylock", "SLAC", "CERN", "Indiana University"], ["Travis Brooks", "Stanford", "SLAC", "CERN"] ],
};

/** 
 * main(): this target fires as soon as the DOM is ready, which may be before
 *         the page download is complete.  Everything else is driven from here.
 */
$(document).ready(
  function() {
    // simple substitution
    updateTableHeader(shared_data);
    updateTableBody(shared_data);
    // event handlers
    addCheckBoxHandlers(shared_data);
    addTextBoxHandlers(shared_data );
    // for DEBUG only; makes working js parse obvious
    $('table').attr("bgcolor", "#91ff91");
  }
);

/**
 * Dynamically create the table columns necessary to hold a list of institutions
 * 
 * @param {Array} inst_list A list of strings representing institution names.
 */
function updateTableHeader(shared_data) {
    var inst_list = shared_data['affiliations']
    var computed_text = '<tr><th>#</th><th>name</th><th>affiliation</th>';
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
    $('#TableHeaders').html(computed_text);

    function activateShowLink(i, inst_list) {
        $('.empty'+i).remove();
        $('.col'+i).show();
    }
    function activateHideLinks(me) {
        var col = me.name;
        var title = me.title.replace("hide", "expand");
        $('.col'+col).before('<td title="'+title+'" class="empty'+col+'" style="border-style: hidden solid hidden solid;"></td>');
        $('.empty'+col).click( function() { activateShowLink(col, inst_list) });
        $('.col'+col).hide();
    }
    $('a.hide_link').click( function() { activateHideLinks(this) });
}

/**
 * Dynamically create the table cells necessary to hold everything
 *
 * @param {Array} author_list A list of author_institution pairs
 * @param {Array} institution_list A list of institutions for checkbox columns
 */
function updateTableBody(shared_data) {
    var author_list = shared_data['authors'];
    var institution_list = shared_data['affiliations'];
    var cols = institution_list.length;
    var even = false;
    var computed_body = '';
    for (var row = 0; row < author_list.length; row++) {

      var row_class = 'row_odd';
      if (even) {
        row_class = 'row_even';
      }
      computed_body += '\n<tr id="table_row_'+row+'" class="'+row_class+' row'+row+'"><td class="rownum">'+ (row+1) +'</td>';

      // name
      computed_body += '<td><input type="text" id="author_'+row+'" value="'+author_list[row][0]+'"></td>';

      // affiliations
      computed_body += '<td><input type="text" id="affils_'+row+'" value="';
      computed_body += author_list[row].slice(1).join(';');
      computed_body += '"></td>';

      // checkboxes
      for (var i = 0; i < institution_list.length; i++) {
        var name = institution_list[i];
        var name_row = name+'_'+row;
        computed_body += '<td><input type="checkbox" name="'+name+'" title="'+institution_list[i];
        computed_body +=           '" class="col'+i+'" id="checkbox_'+row+'_'+i+'" value="'+name_row+'"';
        for (var place = 1; place < author_list[row].length; place++) {
          if (author_list[row][place] == name) {
            computed_body += ' checked';
          }
        }
        computed_body += '></td>';
      }
      computed_body += '</tr>\n';

      even = !even;
    };

    $('#TableContents').html(computed_body);
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
  var authors = shared_data['authors'];
  var myaffils = authors[myrow].slice(1);
  var cb_loc = $.inArray(me.name, myaffils);

  if ((me.checked == true) && (cb_loc == -1)) {
      // we want it, but it's not here
      shared_data['authors'][myrow].push(me.name);
      addCheckBoxHandlers_inputSync(shared_data, myrow, me.name);
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
      addCheckBoxHandlers_inputSync(shared_data, myrow, me.name);
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
  $('input[type="text"]').blur( function() { addTextBoxHandlers_blurHandler(shared_data, this) } );
}

/**
 * Sync the text box to shared_data, then sync shared_data to the checkboxes
 */
function addTextBoxHandlers_blurHandler(shared_data, me) {
  var myrow = me.id.substring(me.id.lastIndexOf('_')+1);
  var myname = shared_data['authors'][myrow][0];
  var newRow = $.map(me.value.split(';'), function(s, i) {
      s = $.trim(s);
      if (s == '') return null;
      else return s;
  });
  me.value = newRow.join(';');
  $.map(shared_data['affiliations'], function(aff, i) {
    $('#checkbox_'+myrow+'_'+i).attr('checked', ($.inArray(aff, newRow) != -1));
  });
  newRow.unshift(myname);
  shared_data['authors'][myrow] = newRow;
}

