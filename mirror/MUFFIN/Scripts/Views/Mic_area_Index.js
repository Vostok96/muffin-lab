
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtEstado: "required",
            txtSeccion: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtEstado: "(*)",
            txtSeccion: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_area,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "area_id" },
            { "data": "area_desc" },
            { "data": "area_seccion" },
            {
                "data": "area_estado", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Activo</span>'
                    } else {
                        return '<span class="badge badge-danger">Inactivo</span>'
                    }
                }
            },
            {
                "data": "area_id", "render": function (data, type, row, meta) {
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
        $("#txtCod").val(json.area_id);
        $("#txtDesc").val(json.area_desc);
        $("#txtEstado").val(json.area_estado == true ? "1" : "0");
        $("#txtSeccion").val(json.area_seccion);
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
                area_id: $("#txtCod").val(),
                area_desc: $("#txtDesc").val(),
                area_estado: $("#txtEstado").val() == 1 ? true : false,
                area_seccion: $("#txtSeccion").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_area,
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

