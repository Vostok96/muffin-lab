
var tabladata;
$(document).ready(function () {

    
    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtNumOrden: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtNumOrden: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_res_comentarios_def,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "rescomen_cod" },
            { "data": "rescomen_desc" },
            { "data": "rescomen_orden" },
            {
                "data": "rescomen_cod", "render": function (data, type, row, meta) {
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
    $("#txtid").val(0);

    if (json != null) {
        $("#txtCod").val(json.rescomen_cod);
        $("#txtDesc").val(json.rescomen_desc);
        $("#txtNumOrden").val(json.rescomen_orden);
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
                rescomen_cod: $("#txtCod").val(),
                rescomen_desc: $("#txtDesc").val(),
                rescomen_orden: $("#txtNumOrden").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_res_comentarios_def,
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

