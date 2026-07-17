
var tabladata;
$(document).ready(function () {

    
    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtCodWhonet: "required",
            txtCodHIS: "required",
            cboTipoMeca: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtCodWhonet: "(*)",
            txtCodHIS: "(*)",
            cboTipoMeca: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_antibiotico,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "atb_id" },
            { "data": "atb_desc" },
            { "data": "atb_homo" },
            { "data": "atb_homo_his" },
            {
                "data": "atb_mecanismo", "render": function (data) {
                    if (data==5) {
                        return 'Antibiótico'
                    }
                    if (data == 1) {
                        return 'Mecanismo de Resistencia'
                    }
                }
            },
            {
                "data": "atb_id_id", "render": function (data, type, row, meta) {
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
        $("#txtid").val(json.atb_id_id);
        $("#txtCod").val(json.atb_id);
        $("#txtDesc").val(json.atb_desc);
        $("#txtCodWhonet").val(json.atb_homo);
        $("#txtCodHIS").val(json.atb_homo_his);        
        $("#cboTipoMeca").val(json.atb_mecanismo);
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
                atb_id_id: $("#txtid").val(),
                atb_id: $("#txtCod").val(),
                atb_desc: $("#txtDesc").val(),
                atb_homo: $("#txtCodWhonet").val(),
                atb_homo_his:$("#txtCodHIS").val(),
                atb_mecanismo:$("#cboTipoMeca").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_antibiotico,
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

