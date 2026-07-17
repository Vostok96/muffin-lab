
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtCodHomo: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtCodHomo: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_muestra,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "muestra_cod_alfa" },
            { "data": "muestra_desc" },
            { "data": "muestra_cod_num" },
            {
                "data": "muestra_cod_alfa", "render": function (data, type, row, meta) {
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
        $("#txtCod").val(json.muestra_cod_alfa);
        $("#txtDesc").val(json.muestra_desc);
        $("#txtCodHomo").val(json.muestra_cod_num);
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
                muestra_cod_alfa: $("#txtCod").val(),
                muestra_desc: $("#txtDesc").val(),
                muestra_cod_num: $("#txtCodHomo").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_muestra,
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

