
var tabladata;
$(document).ready(function () {    
    activarMenu("Mantenedor_con");
    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtHC: "required",
            txtApellidos: "required",
            txtNombres: "required",
            txtFechaNac: "required",
            persona_genero: "required"
        },
        messages: {
            txtHC: "(*)",
            txtApellidos: "(*)",
            txtNombres: "(*)",
            txtFechaNac: "(*)",
            persona_genero: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerPersona,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "persona_hc" },
            { "data": "persona_apellidos" },
            { "data": "persona_nombres" },
            { "data": "persona_fecha_nac" },
            { "data": "persona_genero" },
            { "data": "persona_edad"},
            {
                "data": "persona_id", "render": function (data, type, row, meta) {
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

function _ExportarPersona() {
    window.location.href = $.MisUrls.url._ExportarPersona;
    /*
    jQuery.ajax({
        url: $.MisUrls.url._ExportarPersona,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data) {                
            } else {
                swal("Mensaje", "No se pudo guardar los cambios", "warning")
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });*/
}


function abrirPopUpForm(json) {
    $("#txtid").val(0);
    if (json != null) {
        $("#txtid").val(json.persona_id);
        $("#txtHC").val(json.persona_hc);
        $("#txtApellidos").val(json.persona_apellidos);
        $("#txtNombres").val(json.persona_nombres);
        $("#txtFechaNac").val(json.persona_fecha_nac);
        $("#cboGenero").val(json.persona_genero);
        $("#txtHC").prop("disabled", true);
    } else {
        $("#form").each(function () {
            this.reset();
        });
        $("#txtHC").prop("disabled", false);
    }
    $('#FormModal').modal('show');
}


function Guardar() {
    if ($("#form").valid()) {
        var request = {
            objeto: {
                persona_id: $("#txtid").val(),
                persona_hc: $("#txtHC").val(),
                persona_apellidos: $("#txtApellidos").val(),
                persona_nombres: $("#txtNombres").val(),
                persona_fecha_nac: $("#txtFechaNac").val(),
                persona_genero: $("#cboGenero").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarPersona,
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

