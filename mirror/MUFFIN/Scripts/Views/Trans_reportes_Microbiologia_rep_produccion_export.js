$(document).ready(function () {
    var d = new Date();
    var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
    var f = new Date();
    f.setDate(f.getDate() - 15);
    var fecha_15 = f.getFullYear() + "-" + (f.getMonth() + 1).toString().padStart(2, "0") + "-" + f.getDate().toString().padStart(2, "0");
    $("#orden_fecha_ini").val(fecha_15);
    $("#orden_fecha_fin").val(fecha_actual);

    //OBTENER EXAMEN
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_examen,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#examen_id").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    //selected-options
                    $("<option>").attr({ "value": item.examen_id }).text(item.examen_desc).appendTo("#examen_id");
                })
                //selected-options
                //$('#examen_id').multiSelect();  
                $('#examen_id').multiSelect({
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
        _Microbiologia_rep_produccion_export();
    });
    $('#select-all').click(function () {
        $('#examen_id').multiSelect('select_all');
        return false;
    });
    $('#deselect-all').click(function () {
        $('#examen_id').multiSelect('deselect_all');
        return false;
    });

    
});


function _Microbiologia_rep_produccion_export() {
    var selectedValues = [];
    var selectedValuesIn = ""
    $("#examen_id :selected").each(function () {
        selectedValues.push($(this).val());
    });
    for (k = 0; k < selectedValues.length; k++) {
        selectedValuesIn += "'"+selectedValues[k]+"',"
    }

    if (selectedValues.length > 0) {
        selectedValuesIn = selectedValuesIn.substring(0, selectedValuesIn.length - 1)
    }
    if (selectedValuesIn.length > 1500) {
        selectedValuesIn = "ALL";
    }

    orden_fecha_ini = $('#orden_fecha_ini').val();
    orden_fecha_fin = $('#orden_fecha_fin').val();
    examen_id = selectedValuesIn;
    orden_filtro = $('#orden_filtro').val();

    var url = $.MisUrls.url._Microbiologia_rep_produccion_export + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&examen_id=" + examen_id + "&orden_filtro=" + orden_filtro;
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