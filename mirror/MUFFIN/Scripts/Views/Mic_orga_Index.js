
var tabladata;
$(document).ready(function () {

    
    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtCodWhonet: "required",
            cboGRAM: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtCodWhonet: "(*)",
            cboGRAM: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_orga,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "orga_id" },
            { "data": "orga_desc" },
            { "data": "orga_homo" },
            { "data": "orga_gram" },
            {
                "data": "orga_id_id", "render": function (data, type, row, meta) {
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
        $("#txtid").val(json.orga_id_id);
        $("#txtCod").val(json.orga_id);
        $("#txtDesc").val(json.orga_desc);
        $("#txtCodWhonet").val(json.orga_homo);
        $("#cboGRAM").val(json.orga_gram);
    } else {
        $("#form").each(function () {
            this.reset();
            $("#txtid").val(0);
        });        
    }
    $('#FormModal').modal('show');
}


function Guardar() {

    if ($("#form").valid()) {

        var request = {
            objeto: {
                orga_id_id: $("#txtid").val(),
                orga_id: $("#txtCod").val(),
                orga_desc: $("#txtDesc").val(),
                orga_homo: $("#txtCodWhonet").val(),
                orga_gram: $("#cboGRAM").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_orga,
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

