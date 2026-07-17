
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtRepCodebar: "required",
            txtRepTM: "required",
            txtRepRM: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtRepCodebar: "(*)",
            txtRepTM: "(*)",
            txtRepRM: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_configuracion_general,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "confi_centro_cod" },
            { "data": "confi_centro_desc" },
            {
                "data": "confi_centro_cod", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>"
                },
                "orderable": false,
                "searchable": false,
                "width": "90px"
            }

        ],
        "language": {
            "url": $.MisUrls.url.Url_datatable_spanish
        },
        responsive: true
    });
})


function abrirPopUpForm(json) {
    if (json != null) {
        $("#txtCod").val(json.confi_centro_cod);
        $("#txtDesc").val(json.confi_centro_desc);

        $("#txtPrintNombre").val(json.confi_impresora_nombre);
        $("#txtPrintCantidad").val(json.confi_impresora_cantidad);
        $("#txtPrintAdicional").val(json.confi_impresora_etiqueta_adicional == true ? "1" : "0");

        $("#txtRepTM").val(json.confi_reporte_muestra_toma == true ? "1" : "0");
        $("#txtRepRM").val(json.confi_reporte_muestra_recepcion == true ? "1" : "0");
        $("#txtRepCodebar").val(json.confi_reporte_codebar == true ? "1" : "0");

        $("#txtAnalizadorTiempoConsulta").val(json.confi_analizador_lista_trabajo);
        
        $("#txtCod").prop("disabled", true);
    } else {
        $("#form").each(function () {
            this.reset();
        });
        $("#txtCod").prop("disabled", false);
    }
    $('#FormModal').modal('show');
}


function Guardar() {
    if ($("#form").valid()) {

        var request = {
            objeto: {
                confi_centro_cod: $("#txtCod").val(),
                confi_centro_desc: $("#txtDesc").val(),

                confi_impresora_nombre: $("#txtPrintNombre").val(),
                confi_impresora_cantidad: $("#txtPrintCantidad").val(),
                confi_impresora_etiqueta_adicional: $("#txtPrintAdicional").val() == 1 ? true : false,

                confi_reporte_muestra_toma: $("#txtRepTM").val() == 1 ? true : false,
                confi_reporte_muestra_recepcion: $("#txtRepRM").val() == 1 ? true : false,
                confi_reporte_codebar: $("#txtRepCodebar").val() == 1 ? true : false,

                confi_analizador_lista_trabajo:$("#txtAnalizadorTiempoConsulta").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_configuracion_general,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    $('#FormModal').modal('hide');
                } else {
                    swal("Mensaje", "No se pudo guardar los cambios", "warning")
                }
            },
            error: function (error) {
                console.log(error)
            },
            beforeSend: function () {

            },
        });
    }

}

