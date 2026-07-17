
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",
            txtCodHomo: "required",
            txtSufijo: "required",
            cboArea: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",
            txtCodHomo: "(*)",
            txtSufijo: "(*)",
            cboArea: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_examen,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "examen_id" },
            { "data": "examen_desc" },
            { "data": "examen_cod_homo" },
            { "data": "examen_codebar_sufijo" },
            {
                "data": "examen_analizador_send", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Enviar</span>'
                    } else {
                        return '<span class="badge badge-danger">No Enviar</span>'
                    }
                }
            },
            {
                "data": "examen_recuento", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Si</span>'
                    } else {
                        return '<span class="badge badge-danger">No</span>'
                    }
                }
            },
            { "data": "oMic_area", render: function (data) { return data.area_desc } },
            { "data": "oMic_area", render: function (data) { return data.area_seccion } },
            {
                "data": "examen_id", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_param(" + JSON.stringify(row) + ")'><i class='fas fa-align-left'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_mues(" + JSON.stringify(row) + ")'><i class='fas fa-border-none'></i></button>";
                        
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


    $('tbody#tlbtbodyExaParam').on('click', 'button.btn-primary', function () {
        json_val = $(this).attr('value');
        var json = JSON.parse(json_val);

        $('#FormModal_param_det').modal('show');    
        $("#txtParamDetID").val(json.exaparam_id);  
        $("#txtParamDetOrden").val(json.exaparam_orden);  
        $("#txtParamDetHomo").val(json.exaparam_homo);  
        
        _ObtenerMic_parametro(json.oMic_parametro.parametro_id);
    });

    
    $("#btnAddParamDet").click(function () {
        $('#FormModal_param_det').modal('show');
        $("#formParamDetId").each(function () {
            this.reset();
        });
        _ObtenerMic_parametro(0);
        $("#txtParamDetID").val("0");
    });


    $('tbody#tlbtbodyMuestra').on('click', 'button.btn-primary', function () {
        json_val = $(this).attr('value');
        var json = JSON.parse(json_val);

        $('#FormModal_mues_det').modal('show');
        $("#txtMuestraDetID").val(json.muestra_exa_id);
        $("#cboMuestraFavo").val(json.muestra_exa_favorito == true?"1":"0");
        _ObtenerMic_muestra(json.oMic_muestra.muestra_cod_alfa);
    });

    $("#btnAddMues").click(function () {
        $('#FormModal_mues_det').modal('show');
        $("#formMuestraDetId").each(function () {
            this.reset();
        });
        _ObtenerMic_muestra(0);
        $("#formMuestraDetId").val("0");
    });
    
})


function abrirPopUpForm(json) {
    $("#txtid").val(0);

    if (json != null) {
        $("#txtCod").val(json.examen_id);
        $("#txtDesc").val(json.examen_desc);
        $("#txtCodHomo").val(json.examen_cod_homo);
        $("#txtSufijo").val(json.examen_codebar_sufijo);
        _ObtenerMic_area(json.area_id)
        var valor = 0;
        valor = json.examen_analizador_send == true ? 1 : 0
        $("#cboEnviarAnalizador").val(valor);

        var valor_rec = 0;
        valor_rec = json.examen_recuento == true ? 1 : 0
        $("#cboRecuento").val(valor_rec);

        $("#txtCod").prop("disabled", true);
    } else {
        $("#form").each(function () {
            this.reset();
        });
        $("#txtCod").prop("disabled", false);
        _ObtenerMic_area(0);
    }
    $('#FormModal').modal('show');
}

function abrirPopUpForm_param(json) {
    if (json != null) {
        $("#txtParamExaId").val(json.examen_id);
        $("#txtParamExaDesc").val(json.examen_desc);
        _ObtenerMic_examen_parametro(json.examen_id);
    } else {
        
    }
    $('#FormModal_param').modal('show');
}

function abrirPopUpForm_mues(json) {
    if (json != null) {
        $("#txtMuesExaId").val(json.examen_id);
        $("#txtMuesExaDesc").val(json.examen_desc);
        _ObtenerMic_examen_muestra(json.examen_id);
    } else {

    }
    $('#FormModal_mues').modal('show');
}

function _ObtenerMic_examen_parametro(examen_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_examen_parametro + "?examen_id=" + examen_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.oMic_parametro.parametro_cod + '</td>';
                    html += '<td>' + item.oMic_parametro.parametro_desc + '</td>';
                    html += '<td>' + item.exaparam_orden + '</td>';                    
                    html += "<td><button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    html += ' <button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_examen_parametro(' + item.exaparam_id + ')"><i class="fa fa-trash"></i></button></td>';
                    html += '</tr>';
                });
                $("#tlbtbodyExaParam").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 

function _ObtenerMic_examen_muestra(examen_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_muestra_examenEXA + "?EXA=" + examen_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.oMic_muestra.muestra_cod_alfa + '</td>';
                    html += '<td>' + item.oMic_muestra.muestra_desc + '</td>';
                    html += '<td>' + (item.muestra_exa_favorito == true ? "<span class='badge badge-success'>SI</span>" : "<span class='badge badge-info'>NO</span>") + '</td>';
                    html += "<td><button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    html += ' <button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_muestra_examen(' + item.muestra_exa_id + ')"><i class="fa fa-trash"></i></button></td>';
                    html += '</tr>';
                });
                $("#tlbtbodyMuestra").html(html);
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
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_area,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboArea").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.area_id }).text(item.area_desc).appendTo("#cboArea");
                })
                if (selectec == 0) {
                    $("#cboArea option:first").val()
                } else {
                    $("#cboArea").val(selectec);
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

function _ObtenerMic_parametro(selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_parametro,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboParamDetDesc").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.parametro_id }).text(item.parametro_desc + " (" + item.parametro_cod+")").appendTo("#cboParamDetDesc");
                })
                if (selectec == 0) {
                    $("#cboParamDetDesc option:first").val()
                } else {
                    $("#cboParamDetDesc").val(selectec);
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

function _ObtenerMic_muestra(selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_muestra,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboMuestraDetDesc").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.muestra_cod_alfa }).text(item.muestra_desc).appendTo("#cboMuestraDetDesc");
                })
                if (selectec == 0) {
                    $("#cboMuestraDetDesc option:first").val()
                } else {
                    $("#cboMuestraDetDesc").val(selectec);
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


function Guardar() {

    if ($("#form").valid()) {

        var request = {
            objeto: {
                examen_id: $("#txtCod").val(),
                examen_desc: $("#txtDesc").val(),
                examen_cod_homo: $("#txtCodHomo").val(),

                examen_codebar_sufijo: $("#txtSufijo").val(),
                examen_recuento: parseInt($("#cboRecuento").val()) == 1 ? true : false,
                examen_analizador_send: parseInt($("#cboEnviarAnalizador").val()) == 1 ? true : false,

                area_id: $("#cboArea").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_examen,
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


function _RegistrarMic_examen_parametro() {
    if ($("#form").valid()) {
        var request = {
            objeto: {
                exaparam_id: $("#txtParamDetID").val(),
                exaparam_orden: $("#txtParamDetOrden").val(),
                exaparam_homo: $("#txtParamDetHomo").val(),
                oMic_parametro: {
                    parametro_id: $("#cboParamDetDesc").val()
                },
                oMic_examen: {
                    examen_id: $("#txtParamExaId").val()
                }
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._RegistrarMic_examen_parametro,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_examen_parametro($("#txtParamExaId").val());
                    $('#FormModal_param_det').modal('hide');
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


function _EliminarMic_examen_parametro($exaparam_id) {
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
                url: $.MisUrls.url._EliminarMic_examen_parametro + "?exaparam_id=" + $exaparam_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_examen_parametro($("#txtParamExaId").val());
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




function _RegistrarMic_muestra_examen() {
    if ($("#formMuestraDetId").valid()) {
        var request = {
            objeto: {
                muestra_exa_id: $("#txtMuestraDetID").val(),
                muestra_exa_favorito: $("#cboMuestraFavo").val() == "1"? true:false,
                oMic_muestra: {
                    muestra_cod_alfa: $("#cboMuestraDetDesc").val()
                },
                oMic_examen: {
                    examen_id: $("#txtMuesExaId").val()
                }
            }
        }
        console.log(request);
        jQuery.ajax({
            url: $.MisUrls.url._RegistrarMic_muestra_examen,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_examen_muestra($("#txtMuesExaId").val());
                    $('#FormModal_mues_det').modal('hide');
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


function _EliminarMic_muestra_examen($muestra_exa_id) {
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
                url: $.MisUrls.url._EliminarMic_muestra_examen + "?muestra_exa_id=" + $muestra_exa_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_examen_muestra($("#txtMuesExaId").val());
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

