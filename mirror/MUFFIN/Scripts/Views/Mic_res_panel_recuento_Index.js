
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtOrden: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtOrden: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_res_panel_recuento,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "panel_res_recuento_cod" },
            { "data": "panel_res_recuento_desc" },
            { "data": "panel_res_recuento_orden" },
            {
                "data": "panel_res_recuento_cod", "render": function (data, type, row, meta) {
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
        $("#txtCod").val(json.panel_res_recuento_cod);
        $("#txtDesc").val(json.panel_res_recuento_desc);
        $("#txtOrden").val(json.panel_res_recuento_orden);
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
                panel_res_recuento_cod: $("#txtCod").val(),
                panel_res_recuento_desc: $("#txtDesc").val(),
                panel_res_recuento_orden: $("#txtOrden").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_res_panel_recuento,
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

