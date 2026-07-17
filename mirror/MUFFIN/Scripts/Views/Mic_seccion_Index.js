
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");
    
    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtNombre: "required",
            txtNomen: "required",
            txtCodigo: "required",
            txtAnio: "required",
            txtNumSecuencua: "required"
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
            "url": $.MisUrls.url._ObtenerMic_seccion,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "seccion_nombre" },
            { "data": "seccion_nomenplatura" },
            { "data": "seccion_codigo" },
            { "data": "seccion_anio" },
            { "data": "seccion_numero" },
            {
                "data": "seccion_id", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_exa(" + JSON.stringify(row) + ")'><i class='fas fa-align-left'></i></button>";

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

    $("#btnAddSessionExamen").click(function () {
        $('#FormModal_examen_add').modal('show');
        $("#formSessionExaId").each(function () {
            this.reset();
        });
        _ObtenerMic_examen(0);
    });
})


function abrirPopUpForm(json) {
    if (json != null) {
        $("#txtid").val(json.seccion_id);
        $("#txtNombre").val(json.seccion_nombre);
        $("#txtNomen").val(json.seccion_nomenplatura);
        $("#txtCodigo").val(json.seccion_codigo);
        $("#txtAnio").val(json.seccion_anio);
        $("#txtNumSecuencua").val(json.seccion_numero);
    } else {
        $("#form").each(function () {
            this.reset();
            $("#txtid").val(0);
        });
        $("#txtCod").prop("disabled", false);
    }
    $('#FormModal').modal('show');
}

function abrirPopUpForm_exa(json) {
    $("#formSesExa").each(function () {
        this.reset();
        $("#txtSessionExaId").val(0);
    });

    if (json != null) {
        console.log(json);
        $("#txtSessionExaId").val(json.seccion_id);
        $("#txtSessionDesc").val(json.seccion_nombre);
        _ObtenerMic_seccion_examen(json.seccion_id);
    } else {

    }
    $('#FormModal_Examen').modal('show');
}

function Guardar() {
    if ($("#form").valid()) {
        
        var request = {
            objeto: {
                seccion_id: $("#txtid").val(),
                seccion_nombre: $("#txtNombre").val(),
                seccion_nomenplatura: $("#txtNomen").val(),
                seccion_codigo: $("#txtCodigo").val(),
                seccion_anio: $("#txtAnio").val(),
                seccion_numero: $("#txtNumSecuencua").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_seccion,
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


function _ObtenerMic_seccion_examen(seccion_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_seccion_examen + "?seccion_id=" + seccion_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                $("#tlbtbodySessionExa").html('');
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.examen_id + '</td>';
                    html += '<td>' + item.examen_desc + '</td>';
                    html += '<td><button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_seccion_examen(' + item.secciondet_id + ')"><i class="fa fa-trash"></i></button></td>';
                    html += '</tr>';
                });
                $("#tlbtbodySessionExa").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 

function _ObtenerMic_examen(selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_examen,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboSecccionExamen").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.examen_id }).text(item.examen_desc).appendTo("#cboSecccionExamen");
                })
                if (selectec == 0) {
                    $("#cboSecccionExamen option:first").val()
                } else {
                    $("#cboSecccionExamen").val(selectec);
                }
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 

function _GuardarMic_seccion_examen() {
    if ($("#formSessionExaId").valid()) {

        var request = {
            objeto: {
                secciondet_id: 0,
                examen_id: $("#cboSecccionExamen").val(),
                seccion_id: $("#txtSessionExaId").val()
            }
        }
        
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_seccion_examen,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_seccion_examen($("#txtSessionExaId").val());
                    $('#FormModal_examen_add').modal('hide');
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
function _EliminarMic_seccion_examen(secciondet_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea eliminar el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Sí",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },

        function () {
            jQuery.ajax({
                url: $.MisUrls.url._EliminarMic_seccion_examen + "?secciondet_id=" + secciondet_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_seccion_examen($("#txtSessionExaId").val());
                    } else {
                        swal("Mensaje", "No se pudo eliminar el usuario", "warning")
                    }
                },
                error: function (error) {
                    console.log(error)
                },
                beforeSend: function () {

                },
            });
        });
}

