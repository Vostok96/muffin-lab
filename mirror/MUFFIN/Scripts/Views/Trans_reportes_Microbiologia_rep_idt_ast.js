$(document).ready(function () {
    var d = new Date();
    var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
    var f = new Date();
    f.setDate(f.getDate() - 15);
    var fecha_15 = f.getFullYear() + "-" + (f.getMonth() + 1).toString().padStart(2, "0") + "-" + f.getDate().toString().padStart(2, "0");
    $("#orden_fecha_ini").val(fecha_15);
    $("#orden_fecha_fin").val(fecha_actual);

    //OBTENER ORGANIMOS
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orga,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#microorganismo_id").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.orga_id }).text(item.orga_desc).appendTo("#microorganismo_id");
                });
                $('#microorganismo_id').multiSelect({
                    selectableHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='Buscar...'>",
                    selectionHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='Buscar...'>",
                    afterInit: function (ms) {
                        var that = this,
                            $selectableSearch = that.$selectableUl.prev(),
                            $selectionSearch = that.$selectionUl.prev(),
                            selectableSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selectable:not(.ms-selected)',
                            selectionSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selection.ms-selected';

                        that.qs1 = $selectableSearch.quicksearch(selectableSearchString)
                            .on('keydown', function (e) {
                                if (e.which === 40) {
                                    that.$selectableUl.focus();
                                    return false;
                                }
                            });

                        that.qs2 = $selectionSearch.quicksearch(selectionSearchString)
                            .on('keydown', function (e) {
                                if (e.which == 40) {
                                    that.$selectionUl.focus();
                                    return false;
                                }
                            });
                    },
                    afterSelect: function () {
                        this.qs1.cache();
                        this.qs2.cache();
                    },
                    afterDeselect: function () {
                        this.qs1.cache();
                        this.qs2.cache();
                    }
                });
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
    //OBTENER ANTIBIOTICO
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_antibiotico,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#antibiotico_id").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.atb_id }).text(item.atb_desc).appendTo("#antibiotico_id");
                });
                $('#antibiotico_id').multiSelect({
                    selectableHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='Buscar...'>",
                    selectionHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='Buscar...'>",
                    afterInit: function (ms) {
                        var that = this,
                            $selectableSearch = that.$selectableUl.prev(),
                            $selectionSearch = that.$selectionUl.prev(),
                            selectableSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selectable:not(.ms-selected)',
                            selectionSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selection.ms-selected';

                        that.qs1 = $selectableSearch.quicksearch(selectableSearchString)
                            .on('keydown', function (e) {
                                if (e.which === 40) {
                                    that.$selectableUl.focus();
                                    return false;
                                }
                            });

                        that.qs2 = $selectionSearch.quicksearch(selectionSearchString)
                            .on('keydown', function (e) {
                                if (e.which == 40) {
                                    that.$selectionUl.focus();
                                    return false;
                                }
                            });
                    },
                    afterSelect: function () {
                        this.qs1.cache();
                        this.qs2.cache();
                    },
                    afterDeselect: function () {
                        this.qs1.cache();
                        this.qs2.cache();
                    }
                });
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    $("#btnGenerarreporte").click(function () {
        _Microbiologia_rep_idt_ast_export();
    });

    $('#select-all-micro').click(function () {
        $('#microorganismo_id').multiSelect('select_all');
        return false;
    });
    $('#deselect-all-micro').click(function () {
        $('#microorganismo_id').multiSelect('deselect_all');
        return false;
    });

    $('#select-all-atb').click(function () {
        $('#antibiotico_id').multiSelect('select_all');
        return false;
    });
    $('#deselect-all-atb').click(function () {
        $('#antibiotico_id').multiSelect('deselect_all');
        return false;
    });
    
});


function _Microbiologia_rep_idt_ast_export() {
    var selectedValues_orga = [];
    var selectedValuesIn_orga = ""
    $("#microorganismo_id :selected").each(function () {
        selectedValues_orga.push($(this).val());
    });
    for (k = 0; k < selectedValues_orga.length; k++) {
        selectedValuesIn_orga += "'" + selectedValues_orga[k]+"',"
    }
    if (selectedValues_orga.length > 0) {
        selectedValuesIn_orga = selectedValuesIn_orga.substring(0, selectedValuesIn_orga.length - 1)
    }
    if (selectedValuesIn_orga.length > 1500) {
        selectedValuesIn_orga = "ALL";
    }

    var selectedValues_atb = [];
    var selectedValuesIn_atb = ""
    $("#antibiotico_id :selected").each(function () {
        selectedValues_atb.push($(this).val());
    });
    for (k = 0; k < selectedValues_atb.length; k++) {
        selectedValuesIn_atb += "'" + selectedValues_atb[k] + "',"
    }
    if (selectedValues_atb.length > 0) {
        selectedValuesIn_atb = selectedValuesIn_atb.substring(0, selectedValuesIn_atb.length - 1)
    }
    if (selectedValuesIn_atb.length > 1500) {
        selectedValuesIn_atb = "ALL";
    }
    //console.log(selectedValuesIn_atb);

    orden_fecha_ini = $('#orden_fecha_ini').val();
    orden_fecha_fin = $('#orden_fecha_fin').val();
    orga_id = selectedValuesIn_orga;
    atb_id = selectedValuesIn_atb;

    var url = $.MisUrls.url._Microbiologia_rep_idt_ast_export + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&orga_id=" + orga_id + "&atb_id=" + atb_id;
    popUpObj = window.open(url,
        "ModalPopUp",
        "fullscreen = yes," +
        "toolbar=no," +
        "scrollbars=no," +
        "location=yes," +
        "statusbar=no," +
        "menubar=no," +
        "resizable=yes," +
        "width=100," +
        "height=100," +
        "left = 0," +
        "top= 0"
    );
    popUpObj.focus();
}