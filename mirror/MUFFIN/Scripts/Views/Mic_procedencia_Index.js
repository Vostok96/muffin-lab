
var tabladata;
$(document).ready(function () {

    
    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtCodHomo: "required",
            txtCodHomoWhonet: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtCodHomo: "(*)",
            txtCodHomoWhonet: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_procedencia,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "procedencia_id" },
            { "data": "procedencia_desc" },
            { "data": "procedencia_cod_homo" },
            { "data": "procedencia_cod_homo_whonet" },
            {
                "data": "procedencia_id", "render": function (data, type, row, meta) {
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
        $("#txtCod").val(json.procedencia_id);
        $("#txtDesc").val(json.procedencia_desc);
        $("#txtCodHomo").val(json.procedencia_cod_homo);
        $("#txtCodHomoWhonet").val(json.procedencia_cod_homo_whonet);
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
                procedencia_id: $("#txtCod").val(),
                procedencia_desc: $("#txtDesc").val(),
                procedencia_cod_homo: $("#txtCodHomo").val(),
                procedencia_cod_homo_whonet:$("#txtCodHomoWhonet").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_procedencia,
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

