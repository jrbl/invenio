/**********************
 * See: http://jsdoc.sourceforge.net/
 **********************/

/** 
 * NB: Initialization values for debug purposes only.
 */
shared_data = {
  'affiliations': [],             // list of institutions present in this data
  'valid_affils': [],             // list of possible institutional affiliations
  'authors':      [ [], ],        // set of all [author, affiliation1, affiliation2 ...]
  'folded':       [],             // which columns are currently hidden
  'row_cut':      [],             // the row recently removed from the data set with 'cut'
};

/** 
 * main: this target fires as soon as the DOM is ready, which may be before
 *       the page download is complete.  Everything else is driven from here.
 */
$(document).ready(
  function() {
    // environment initialization/table building
    initTable(shared_data);
    initKeystrokes(shared_data);

    // startup behaviors
    $('#affils_0').focus()

    // for DEBUG only; makes working js parse obvious
    $('table').attr("bgcolor", "#FF66FF");

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
        if (label.length > 10) {                 // XXX: 10 is magic number here and elsewhere in this loop
            sliced = label.slice(0,7)+'...';
        } else {
            sliced = label;
            for (var j = 10 - label.length; j > 0; j--) {
                sliced += '&nbsp;';
            }
        }
        label = (i+1).toString() + '. ' + label;
        sliced = '<span class="column_no" style="font-size: .4em;">'+(i+1).toString() + '</span><br />' + sliced; // XXX: inline styling
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
  $('input[type="checkbox"]').click( function() { addCheckBoxHandlers_changeHandler(shared_data, this.value, this.checked) } );
}

/**
 * Search the affiliations for an author looking for this checkbox.
 */
function addCheckBoxHandlers_changeHandler(shared_data, myvalue, mystatus) {
  var myrow = myvalue.substring(myvalue.lastIndexOf('_')+1);
  var myaffils = shared_data['authors'][myrow].slice(1);
  var myname = myvalue.slice(0, myvalue.indexOf('_'));
  var cb_loc = $.inArray(myname, myaffils);

  if ((mystatus == true) && (cb_loc == -1)) {
      // we want it, but it's not here
      shared_data['authors'][myrow].push(myname);
      addCheckBoxHandlers_inputSync(shared_data, myrow, myname);
  } else if ((mystatus == true) && (cb_loc != -1)) {
      // we want it, but it's already here
      return;
  } else if ((mystatus == false) && (cb_loc == -1)) {
      // we don't want it, and it's not here
      return;
  } else if ((mystatus == false) && (cb_loc != -1)) {
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
  shared_data['authors'][row][0] = escapeHTML(value);
  updateTable(shared_data);
}

/**
 * Sync the affiliations box to shared_data, then sync shared_data to the checkboxes
 */
function addAffilBoxHandlers_changeHandler(shared_data, row, value) {
  var myname = shared_data['authors'][row][0];
  var newRow = jQuery.map(value.split(';'), function(s, v) {
      s = jQuery.trim(s);
      if (s == '') return null;   /* drop empty strings */
      else return escapeHTML(s);  /* otherwise, sanitize & return */
  });
  for (var i in newRow) {
      var datum = newRow[i];
      var iDatum = parseInt(datum);
      /* column number given */
      if ((iDatum == datum-0) &&       // small int w/ no junk chars
          (iDatum > 0) &&              // more than 1
          (iDatum <= shared_data['affiliations'].length)) {     // less max + 1
          newRow[i] = shared_data['affiliations'][datum-1];
      } else {
          /* unseen values get added as new columns */
          if (jQuery.inArray(datum, shared_data['affiliations']) == -1) {
            shared_data['affiliations'].push(datum);
          }
      }
  }
  value = newRow.join(';');
  newRow.unshift(myname);
  shared_data['authors'][row] = newRow;
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

/**
 * Bind keyboard events to particular keystrokes; called after table initialization3
 */
function initKeystrokes(shared_data) {
    var keybindings = {
        /*'tab'     : ['Move forward through affiliations', 
                     'tab', 
                     keystrokeTab,
                     {extra_data: shared_data}],
//                     '#TableContents input[type="text"]'],
        'stab'    : ['Move backward through affiliations', 
                     'shift+tab', 
                     keystrokeTab,
                     {extra_data: shared_data},
                     '#TableContents input[type="text"]'],  */
        //'enter'   : ['Accept this field and move to the next.',
        //             'alt+ctrl+shift+e',
        //             keystrokeEnter,
        //             {extra_data: shared_data}],
        'submit'  : ['Submit the changes.  No input field should be selected.', 
                     'alt+ctrl+shift+s', 
                     function(event) { 
                         $('#submit_button').click();  
                         event.preventDefault(); }],
        'cutRow'  : ['Cut this author row.',
                     'alt+ctrl+shift+x',
                     updateTableCutRow,
                     {extra_data: shared_data}],
        'copyRow' : ['Copy this author row.',
                     'alt+ctrl+shift+c',
                     updateTableCopyRow,
                     {extra_data: shared_data}],
        'pasteRow': ['Paste an author row after this row.',
                     'alt+ctrl+shift+v',
                     updateTablePasteRow,
                     {extra_data: shared_data}],
        'suggest' : ['Auto-suggest affiliations based on this value.',
                     'alt+ctrl+shift+a',
                     validateAffiliation,
                     {extra_data: shared_data}],
    };

    jQuery.each(keybindings, function(junk, val) {
        data_dictionary = {combi: val[1]};
        target = document;
        if (val.length >= 4) {
            for (key in val[3]) {
                data_dictionary[key] = val[3][key];
            }
        } 
        if (val.length >= 5) {
            target = val[4];
        }
        $(document).bind('keypress', data_dictionary, val[2]);
        //$(target).bind('keypress', data_dictionary, val[2]);
    });

    // Extra stuff worth doing 
    $('#submit_button').attr('title', keybindings['submit'][1] + ' to Submit');

}

/** 
* Remove a row from the displayed table and put its data onto a holding stack.
 * 
 * @param {Event} event The javascript event object associated with this cut.
 */
function updateTableCutRow(event) {
    var target_id = event.target.getAttribute('id');
    var row_element = event.target.parentNode.parentNode;
    var row = $('#TableContents tr').index(row_element);
    var shared_data = event.data.extra_data;

    if ((row < 0) || (row > (shared_data.length -1)))
        return
    shared_data['row_cut'] = shared_data['authors'][row];

    updateTableCopyRow(event);
    shared_data['authors'].splice(row, 1);
    updateTable(shared_data);
    if (row == $('#TableContents tr').length) {
        tag = target_id.slice(0, target_id.lastIndexOf('_')+1);
        $('#'+tag+row).focus();
    } else
        $('#'+target_id).focus();
    event.preventDefault();
}

/** 
 * Insert a row from the holding stack onto the displayed table.
 * 
 * @param {Event} event The javascript event object associated with this paste.
 */
function updateTablePasteRow(event) {
    var target_id = event.target.getAttribute('id');
    var row_element = event.target.parentNode.parentNode;
    var row = $('#TableContents tr').index(row_element) +1;
    var shared_data = event.data.extra_data;
    var cut = shared_data['row_cut'];

    if ((row < 1) || (row > shared_data.length))
        return
    if (cut == null)
        return
    shared_data['authors'].splice(row, 0, cut);
    updateTable(shared_data);
    $('#'+target_id).focus();
    event.preventDefault();
}

/** 
 * Put a row's data onto a holding stack.
 * 
 * @param {Event} event The javascript event object associated with this copy.
 */
function updateTableCopyRow(event) {
    var target_id = event.target.getAttribute('id');
    var row_element = event.target.parentNode.parentNode;
    var row = $('#TableContents tr').index(row_element);
    var shared_data = event.data.extra_data;

    if ((row < 0) || (row > (shared_data.length -1)))
        return
    shared_data['row_cut'] = shared_data['authors'][row];
    event.preventDefault();
}

function validateAffiliation(event) {
    //var shared_data = event.data.extra_data;
    /* Get the affiliations in the box */
    var target_id = event.target.getAttribute('id');
    var row = target_id.slice(target_id.indexOf('_')+1);
    $('#'+target_id).change();
      // sometimes the value may not update properly.  XXX Until that is fixed, this will do
    var target_af = shared_data['authors'][row].slice(1);

    /* NB: The logic is turned on its head.  I want to say, "post this value,
       get the result, then do some processing on the result."  But because the
       post results can return at any time, I have to define the processing I 
       want to do first, then call that from within the callback for the post */
    function processPost(data, idx) {
        idx += 1;
        if (data.length == 1) {
            shared_data['authors'][row][idx] = data[0];
            //$('#'+target_id).change();
            updateTable(shared_data);
        } else if (data.length > 1) {
            $('#'+target_id).addClass('doubtful');
        }
        // intentionally do nothing on empty list
    }

    for (var i = 0; i < target_af.length; i++) {
        if (jQuery.inArray(target_af[i], shared_data['valid_affils'])) {

          jQuery.post('checkAffil', 
                      {'affil': target_af[i], 'idx': i}, 
                      function (data, textStatus) {
                          var idx = parseInt(this.data.slice(this.data.indexOf('idx=')+4));
                          processPost(data, idx);
                      },
                      // XXX: 'json' is bad practice, but we trust the server and it's convenient
                      'json');              

        } else {
            /* if affiliation not in shared_data['valid_affils'] decorate questionable */
            $('#'+target_id).addClass('doubtful');
        }
    }
}

/*****************************************************************************************************
 ********** busted **************
 *****************************************************************************************************/
/**
 * Handle key tab (save content and jump to next content field).
 */
function keystrokeTab(event){
    var entryCells = $('#TableContents input[type="text"]');
    var element = event.target;
    var element_i = $(entryCells).index(element);
    var end_i = $(entryCells).size() - 1;
    var shared_data = event.data.extra_data;
    var move = 1;

    if (event.shiftKey) {
        if (element_i == 0)
            move = end_i;
        else
            move = -1;
    } else {
        if (element_i == end_i)
            move = -end_i;
        else
            move = 1;
    }

    //$(entryCells).eq(element_i)[0].blur();
    //$(entryCells).eq(element_i)[0].triggerHandler("blur");
    //addAffilBoxHandlers_blurHandler(shared_data, $(entryCells).eq(element_i)[0]);
    $(entryCells).eq(element_i+move).focus();
    ///$('#'+tag+'_'+move).focus();

    //$(entryCells).eq(element_i+move).triggerHandler("focus");
    //for (key in $(entryCells).eq(element_i)[0])
        //document.write(key + '<br />\n');
        //document.write($(entryCells).eq(element_i).val)
    event.preventDefault();
}

function keystrokeEnter(event) {
    var target_id = event.target.getAttribute('id');
    var row_element = event.target.parentNode.parentNode;
    var row = $('#TableContents tr').index(row_element);
    var shared_data = event.data.extra_data;

    if ((row < 0) || (row > (shared_data.length -1)))
        return

    //var target_row = target_id.slice(target_id.lastIndexOf('_')+1);
    //var next_row = target_row + 1;
    var next_id = target_id.slice(0, target_id.lastIndexOf('_')+1) + (row+1);

    $(target_id).change();
    $(next_id).focus(); 
    event.preventDefault();
}

