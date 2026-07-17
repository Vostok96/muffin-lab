var tabladata;
$(document).ready(function () {

    activarMenu("Mantenedor_con");

    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtDesc: "required",
            txtTipo: "required",
            txtColor: "required",
            txtEstado: "required",
            txtOrden: "required",
            txtVerifica:"required"
        },
        messages: {
            txtDesc: "(*)",
            txtTipo: "(*)",
            txtColor: "(*)",
            txtEstado: "(*)",
            txtOrden: "(*)",
            txtVerifica: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_destinos,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "destinos_desc" },
            { "data": "destinos_tipo" },
            { "data": "destinos_color" },
            { "data": "destinos_orden_verificacion_orden" },
            {
                "data": "destinos_orden_verificacion_requiere", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">SI</span>'
                    } else {
                        return '<span class="badge badge-danger">NO</span>'
                    }
                }
            },
            {
                "data": "destinos_estado", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Activo</span>'
                    } else {
                        return '<span class="badge badge-danger">Inactivo</span>'
                    }
                }
            },
            {
                "data": "destinos_id", "render": function (data, type, row, meta) {
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
        $("#txtId").val(json.destinos_id);
        $("#txtDesc").val(json.destinos_desc);
        $("#txtTipo").val(json.destinos_tipo);
        $("#txtColor").val(json.destinos_color);

        $("#txtOrden").val(json.destinos_orden_verificacion_orden);
        $("#txtVerifica").val(json.destinos_orden_verificacion_requiere == true ? "1" : "0");

        $("#txtEstado").val(json.destinos_estado == true ? "1" : "0");
    } else {
        $("#form").each(function () {
            this.reset();
            $("#txtId").val(0);
        });
    }
    $('#FormModal').modal('show');
}


function Guardar() {
    if ($("#form").valid()) {

        var request = {
            objeto: {
                destinos_id: $("#txtId").val(),
                destinos_desc: $("#txtDesc").val(),
                destinos_tipo: $("#txtTipo").val(),
                destinos_color: $("#txtColor").val(),
                destinos_estado: $("#txtEstado").val() == 1 ? true : false,

                destinos_orden_verificacion_orden: $("#txtOrden").val(),
                destinos_orden_verificacion_requiere: $("#txtVerifica").val() == 1 ? true : false
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_destinos,
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

