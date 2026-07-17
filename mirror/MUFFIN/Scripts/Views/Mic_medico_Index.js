
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCole: "required",
            txtNombres: "required",
            txtApellidos: "required",
            txtEstado: "required"
        },
        messages: {
            txtCole: "(*)",
            txtNombres: "(*)",
            txtApellidos: "(*)",
            txtEstado: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_medico,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "medico_colegiatura" },
            { "data": "medico_apellidos" },
            { "data": "medico_nombres" },
            {
                "data": "medico_estado", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Activo</span>'
                    } else {
                        return '<span class="badge badge-danger">Inactivo</span>'
                    }
                }
            },
            {
                "data": "medico_id", "render": function (data, type, row, meta) {
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
        $("#txtCole").val(json.medico_colegiatura);
        $("#txtNombres").val(json.medico_nombres);
        $("#txtApellidos").val(json.medico_apellidos);
        $("#txtEstado").val(json.medico_estado==true?"1":"0");
        $("#txtCole").prop("disabled", true);
    } else {
        $("#form").each(function () {
            this.reset();
        });
        $("#txtCole").prop("disabled", false);
    }
    $('#FormModal').modal('show');
}


function Guardar() {
    if ($("#form").valid()) {

        var request = {
            objeto: {
                medico_colegiatura: $("#txtCole").val(),
                medico_nombres: $("#txtNombres").val(),
                medico_apellidos: $("#txtApellidos").val(),
                medico_estado: $("#txtEstado").val() == 1 ? true : false
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_medico,
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

