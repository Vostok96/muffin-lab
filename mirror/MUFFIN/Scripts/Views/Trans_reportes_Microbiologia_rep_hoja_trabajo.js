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
    _AbrirVentanaAutorizada(url, "Hoja de trabajo", 1000, 700);
    LoadModalDiv();
}

function _AbrirVentanaAutorizada(url, titulo, ancho, alto) {
    var token = localStorage.getItem("muffin_token") || "";
    var popUpObj = window.open("", "ModalPopUp", "toolbar=no,scrollbars=yes,location=yes,statusbar=no,menubar=no,resizable=yes,width=" + ancho + ",height=" + alto + ",left=0,top=0");
    if (!popUpObj) { return; }
    popUpObj.document.write("<!doctype html><html><head><meta charset='utf-8'><title>" + titulo + "</title></head><body style='font-family:Arial,sans-serif;padding:24px;color:#294c52'>Generando reporte...</body></html>");
    popUpObj.document.close();
    fetch(url, { headers: token ? { "Authorization": "Bearer " + token } : {} })
        .then(function (response) { if (!response.ok) { throw new Error("No se pudo generar el reporte"); } return response.text(); })
        .then(function (html) { popUpObj.document.open(); popUpObj.document.write(html); popUpObj.document.close(); popUpObj.focus(); })
        .catch(function (error) { popUpObj.document.open(); popUpObj.document.write("<strong>" + error.message + "</strong>"); popUpObj.document.close(); });
}
