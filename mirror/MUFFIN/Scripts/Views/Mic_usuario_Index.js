
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
            "url": $.MisUrls.url._ObtenerMic_usuario,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "usuario_id" },
            { "data": "usuario_apellidos" },
            { "data": "usuario_nombres" },
            {
                "data": "usuario_estado", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Activo</span>'
                    } else {
                        return '<span class="badge badge-danger">No Activo</span>'
                    }
                }
            },
            {
                "data": "usuario_rol", render: function (data) {
                    if (data == 1) {
                        return 'Admin - Super'
                    }
                    if (data == 2) {
                        return 'Admin - Usuario Procesos'
                    }
                    if (data == 3) {
                        return 'Usuario - Procesos'
                    }
                    if (data == 4) {
                        return 'Usuario - Ingreso / Consultas'
                    }
                    if (data == 5) {
                        return 'Usuario - Consultas'
                    }
                    if (data == 6) {
                        return 'Usuario - Toma de Muestras'
                    }
                    if (data == 7) {
                        return 'Médico - Consultas'
                    }
                }
            },
            {
                "data": "usuario_id", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_area_permiso(" + JSON.stringify(row) + ")'><i class='fas fa-align-left'></i></button>";
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


    $('tbody#tlbtbodyAreaPermiso').on('click', 'button.btn-primary', function () {
        json_val = $(this).attr('value');
        var json = JSON.parse(json_val);
        $('#FormModal_area').modal('show');
        /*$("#FormModal_area").each(function () {
            this.reset();
        });*/

        $("#txtAreaAreaPerId").val(json.areaper_id);
        $("#cbAreaValidacionPreliminar").val(json.areaper_validacion_preliminar == true ? 1 : 0);
        $("#cbAreaValidacionFinal").val(json.areaper_validacion_final == true ? 1 : 0);

        _ObtenerMic_area(json.area_id);
    });

    $("#btnAddArea").click(function () {
        $('#FormModal_area').modal('show');
        $("#formArea").each(function () {
            this.reset();
        });
        _ObtenerMic_area(0);
        $("#txtAreaAreaPerId").val("0");
    });
    
})


function abrirPopUpForm(json) {
    if (json != null) {
        $("#txtCod").val(json.usuario_id);
        $("#txtCod").prop("disabled", true);

        $("#txtApe").val(json.usuario_apellidos);
        $("#txtNom").val(json.usuario_nombres);
        $("#cbEstado").val(json.usuario_estado == true?"1":"0");
        $("#cbRol").val(json.usuario_rol);
        $("#txtCodHomo").val(json.usuario_cod_homo);   
        $("#txtPass").val("");  
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
                usuario_id: $("#txtCod").val(),
                usuario_apellidos: $("#txtApe").val(),
                usuario_nombres: $("#txtNom").val(),
                usuario_estado: $("#cbEstado").val() == "1" ? true : false,
                usuario_rol: $("#cbRol").val(),
                usuario_cod_homo: $("#txtCodHomo").val(),
                usuario_pass: $("#txtPass").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_usuario,
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



function abrirPopUpForm_area_permiso(json) {
    if (json != null) {
        $("#txtAreaUserId").val(json.usuario_id);
        
        $("#txtAreaUserDesc").val(json.usuario_apellidos+" " + json.usuario_nombres);
        _ObtenerMic_area_permiso(json.usuario_id);
    } 
    $('#FormModal_area_permiso').modal('show');
}




function _ObtenerMic_area_permiso(usuario_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_area_permiso + "?usuario_id=" + usuario_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            console.log(data);
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.oMic_area.area_id + '</td>';
                    html += '<td>' + item.oMic_area.area_desc + '</td>';
                    html += "<td><button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    html += ' <button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_area_permiso(' + item.areaper_id + ')"><i class="fa fa-trash"></i></button></td>';
                    html += '</tr>';
                });
                $("#tlbtbodyAreaPermiso").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 


function _ObtenerMic_area(selectec) {
    //OBTENER
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_area,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cbAreaAreaId").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.area_id }).text(item.area_desc).appendTo("#cbAreaAreaId");
                })
                if (selectec == 0) {
                    $("#cbAreaAreaId option:first").val()
                } else {
                    $("#cbAreaAreaId").val(selectec);
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


function _GuardarMic_area_permiso() {
    if ($("#formArea").valid()) {
        var request = {
            objeto: {
                areaper_id: $("#txtAreaAreaPerId").val(),

                areaper_validacion_preliminar: $("#cbAreaValidacionPreliminar").val() == 1 ? true:false,
                areaper_validacion_final: $("#cbAreaValidacionFinal").val() == 1 ? true:false,

                area_id: $("#cbAreaAreaId").val(),
                usuario_id: $("#txtAreaUserId").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_area_permiso,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_area_permiso($("#txtAreaUserId").val());
                    $('#FormModal_area').modal('hide');
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

function _EliminarMic_area_permiso($areaper_id) {
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
                url: $.MisUrls.url._EliminarMic_area_permiso + "?areaper_id=" + $areaper_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_area_permiso($("#txtAreaUserId").val());
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

