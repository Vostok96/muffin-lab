$(document).ready(function () {

    //OBTENER EXAMEN
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_seccion,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#examen_id").html('');
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.seccion_id }).text(item.seccion_nombre).appendTo("#examen_id");
                })
                $("#examen_id").val($("#examen_id option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    $("#btnExport").click(function () {
        _Microbiologia_rep_hoja_trabajo_export_Trans_reportes($("#orden_fecha_ini").val(), $("#orden_fecha_fin").val(), $("#examen_id").val(), $("#examen_id option:selected").text());
    });
});

function _Microbiologia_rep_hoja_trabajo_export_Trans_reportes(orden_fecha_ini, orden_fecha_fin, seccion_id, seccion_nombre) {

    var url = $.MisUrls.url._Microbiologia_rep_hoja_trabajo_export_Trans_reportes + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&seccion_id=" + seccion_id + "&seccion_nombre=" + seccion_nombre;
    popUpObj = window.open(url,
        "ModalPopUp",
        "fullscreen = yes," +
        "toolbar=no," +
        "scrollbars=no," +
        "location=yes," +
        "statusbar=no," +
        "menubar=no," +
        "resizable=yes," +
        "width=800," +
        "height=400," +
        "left = 0," +
        "top= 0"
    );
    popUpObj.focus();
    LoadModalDiv();
}
