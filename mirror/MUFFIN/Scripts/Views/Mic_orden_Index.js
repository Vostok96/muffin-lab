
var tabladata;
var posicion_frame = 0;
const posicion_frame_data = [];
var session_user_rol = $("#session_user_rol").val();
var muestrasExamenActual = [];

$(document).ready(function () {   

    var d = new Date();
    var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
    
    var f = new Date();
    f.setDate(f.getDate() - 10);
    
    var fecha_15 = f.getFullYear() + "-" + (f.getMonth() + 1).toString().padStart(2, "0") + "-" + f.getDate().toString().padStart(2, "0");

    $("#txtfechaInicio").val(fecha_15);
    $("#txtfechaFin").val(fecha_actual);

    activarMenu("Mantenedor_orden");

    function calcEdad(fechaNac){
        if(!fechaNac){return "";}
        var hoy=new Date();
        var nac=new Date(fechaNac+"T00:00:00");
        var edad=hoy.getFullYear()-nac.getFullYear();
        var m=hoy.getMonth()-nac.getMonth();
        if(m<0||(m===0&&hoy.getDate()<nac.getDate())){edad--;}
        return edad>=0?edad+"":"";
    }
    window._calcEdad=calcEdad;

    $("#txtFechaNac").on("change",function(){
        $("#txtEdad").val(calcEdad($(this).val()));
    });

    $("#cboMedico").prop("disabled",true);
        
    $("#btnBuscarHC").click(function () {
        _ObtenerIDPersona($("#txtHC").val());
    });

    listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
    $("#btnBuscar").click(function () {
        var table = $('#tbdata').DataTable();
        table.destroy();
        listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
    });

    $("#txtBuscar").keypress(function (e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code == 13) {
            var table = $('#tbdata').DataTable();
            table.destroy();
            listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
        }
    });
    

    //_ObtenerIDPersona("DNI_FICTICIO");
    //OBTENER PROCEDECNIA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_procedencia,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboProcedencia").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.procedencia_uuid }).text(item.procedencia_desc).appendTo("#cboProcedencia");
                })
                $("#cboProcedencia").val($("#cboProcedencia option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });


    //OBTENER SERVICIO
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_servicio,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboServicio").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.servicio_uuid }).text(item.servicio_desc).appendTo("#cboServicio");
                })
                $("#cboServicio").val($("#cboServicio option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    //OBTENER EXAMEN
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_examen,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboExamen").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.examen_id }).text(item.examen_desc).appendTo("#cboExamen");
                })
                $("#cboExamen").val($("#cboExamen option:first").val());
                cboMuetsraEXA($("#cboExamen option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_medico,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboMedico").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.medico_id }).text(item.medico_apellidos + " " + item.medico_nombres).appendTo("#cboMedico");
                })
                $("#cboMedico").val($("#cboMedico option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    $('#cboExamen').change(function () {
        var value = $(this).val();
        cboMuetsraEXA(value, null);
    });

    $('#cboTipoMuestra').change(function () {
        actualizarTipoMuestraNivel2(null);
    });

    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtHC: "required",
            txtApellidos: "required",
            txtNombres: "required",
            txtFechaNac: "required",
            cboGenero: "required",

            txtFechaOrden: "required",
            txtNumeroOrden: "required",

            cboEstado: "required",
            cboProcedencia: "required",
            cboServicio: "required",
            cboExamen: "required",
            //txtCodigoBarras: "required",

            cboTipoMuestra: "required",
            txtFechaTomaMuestra: "required",
            txtFechaRecepcionMuestra: "required"            
        },
        messages: {
            txtHC: "(*)",
            txtApellidos: "(*)",
            txtNombres: "(*)",
            txtFechaNac: "(*)",
            cboGenero: "(*)",

            txtFechaOrden: "(*)",
            txtNumeroOrden: "(*)",

            cboEstado: "(*)",
            cboProcedencia: "(*)",
            cboServicio: "(*)",
            cboExamen: "(*)",
            //txtCodigoBarras: "(*)",

            cboTipoMuestra: "(*)",
            txtFechaTomaMuestra: "(*)",
            txtFechaRecepcionMuestra: "(*)"
        },
        errorElement: 'span'
    });

    $('tbody#tlbtbodyOrdenExamen').on('click', 'button.btn-primary', function () {
        json_val = $(this).attr('value');
        var json = JSON.parse(json_val);
        $('#FormModal_examenes').modal('show');
        $("#cboExamen").val(json.oMic_examen.examen_id);
        $("#txtCodigoBarras").val(json.orden_det_codebar);
        $("#cboExamen").prop('disabled', true);
        cboMuetsraEXA(json.oMic_examen.examen_id, json.oMic_muestra.muestra_id);
        $("#txComentariosMuestra").val(json.orden_det_muestra_comentarios);
        $("#txtFechaTomaMuestra").val(json.fecha_muestra_toma);
        $("#txtFechaRecepcionMuestra").val(json.fecha_muestra_recepcion);
    });



    //////////////////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////
    $("#btnFramPrimero").click(function () {        
        posicion_frame = 0;
        rec_abrirPopUpForm(posicion_frame);
    });
    $("#btnFramAnterior").click(function () {
        if (posicion_frame > 0) {
            posicion_frame--;
            rec_abrirPopUpForm(posicion_frame);
        }
    });
    $("#btnFramSiguiente").click(function () {
        if (posicion_frame < posicion_frame_data.length-1) {
            posicion_frame++;
            rec_abrirPopUpForm(posicion_frame);
        }
    });
    $("#btnFramUltimo").click(function () {        
        posicion_frame = (posicion_frame_data.length - 1);
        rec_abrirPopUpForm(posicion_frame);
    });
    //////////////////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////

    $("#btnComentariosMuestra").click(function () {
        _ObtenerSecuenciaMic_seccion($("#cboExamen").val());//txComentariosMuestra
    });

    $("#txtEdad").on("change", function () {
        if ($(this).val()!='') {
            var d = new Date();
            d.setDate(d.getDate() - ($(this).val() * 365));            
            var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
            $("#txtFechaNac").val(fecha_actual);
        }
    });
})


function _ObtenerSecuenciaMic_seccion(examen_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerSecuenciaMic_seccion + "?examen_id=" + examen_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("#txComentariosMuestra").val(item.seccion_codigo);
                });
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 
function listarRistros(orden_fecha_ini, orden_fecha_fin, orden_buscar) {
    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_orden + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&orden_buscar=" + orden_buscar,//orden_fecha_ini, orden_fecha_fin, orden_buscar
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "orden_fecha" },
            { "data": "orden_numero" },

            { "data": "oMic_persona", render: function (data) { return data.persona_hc } },
            { "data": "oMic_persona", render: function (data) { return data.persona_apellidos + ", " + data.persona_nombres} },

            { "data": "oMic_procedencia", render: function (data) { return data.procedencia_desc} },
            { "data": "oMic_servicio", render: function (data) { return data.servicio_desc} },

            {
                "data": "orden_estado", "render": function (data) {
                    if (data) {
                        return '<span class="badge badge-success">Activo</span>'
                    } else {
                        return '<span class="badge badge-danger">No Activo</span>'
                    }
                }
            },
            {
                "data": "orden_id", "render": function (data, type, row, meta)
                {
                    posicion_frame_data[meta.row] = (JSON.stringify(row));
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='rec_abrirPopUpForm_ini(" + JSON.stringify(row.orden_id) + ")'><i class='fas fa-pen'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_det(" + JSON.stringify(row) + ")'><i class='fas fa-align-left'></i></button>"

                        + " <button class='btn btn-warning btn-sm' type='button' onclick='_RegistrarPrinterCodebarMic_orden(" + row.orden_id + ")'><i class='fas fa-barcode'></i></button>"

                        + (row.concat_temp_numero_examenes == 0 ? "" : " <span class='badge badge-success' style='font-size: xx-small;'>E(" + row.concat_temp_numero_examenes+")</span>")
                        + (row.concat_temp_res_resultado == 0 ? "" : "<span class='badge badge-primary' style='font-size: xx-small;'>GU(" + row.concat_temp_res_resultado + ")</span>")
                        + (row.concat_temp_res_priliminar == 0 ? "" : "<span class='badge badge-warning' style='font-size: xx-small;'>VP(" + row.concat_temp_res_priliminar + ")</span>")
                        + (row.concat_temp_res_final == 0 ? "" : "<span class='badge badge-success' style='font-size: xx-small;'>VF(" + row.concat_temp_res_final + ")</span>");

                },
                "orderable": false,
                "searchable": false,
                "width": "90px"
            }

        ],
        "language": {
            "url": $.MisUrls.url.Url_datatable_spanish
        },
        "order": [[0, "desc"]],
        responsive: true
    });

    $("#btnAddOrdenExamenAdd").click(function () {
        $('#FormModal_examenes').modal('show');
        $("#form_axamenes").each(function () {
            this.reset();
            $("#cboExamen").prop('disabled', false);
        });
        var d = new Date();
        var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
        $("#txtFechaTomaMuestra").val(fecha_actual + "T" + d.getHours() + ":00");
        $("#txtFechaRecepcionMuestra").val(fecha_actual + "T" + d.getHours() + ":00");
    });
}

function rec_abrirPopUpForm_ini(orden_id) {
    if (orden_id) {
        for (k = 0; k < posicion_frame_data.length; k++) {
            var json = JSON.parse(posicion_frame_data[k]);
            if (json.orden_id == orden_id) {
                rec_abrirPopUpForm(k);
            }
        }        
    }
}

function rec_abrirPopUpForm(posicion) {
    posicion_frame = posicion;
    if (posicion >= 0) {
        var json = JSON.parse(posicion_frame_data[posicion]);
        abrirPopUpForm(json);
    }
}

function abrirPopUpForm(json) {
    if (json != null) {        
        $("#txtOrdenId").val(json.orden_id);
        $('.cl_ocultar_nuevo').show();
        $("#txtHC").val(json.oMic_persona.persona_hc);
        $("#txtApellidos").val(json.oMic_persona.persona_apellidos);
        $("#txtNombres").val(json.oMic_persona.persona_nombres);
        $("#txtFechaNac").val(json.oMic_persona.persona_fecha_nac);
        $("#cboGenero").val(json.oMic_persona.persona_genero);
        $("#txtEdad").val(window._calcEdad(json.oMic_persona.persona_fecha_nac));

        $("#txtFechaOrden").val(json.orden_fecha);
        $("#txtNumeroOrden").val(json.orden_numero);
        $("#txtFechaOrden").prop('disabled', true);
        $("#txtNumeroOrden").prop('disabled', true);
        var valor = 0;
        valor = json.orden_estado == true ? 1 : 0
        $("#cboEstado").val(valor);
        
        $("#cboProcedencia").val(json.oMic_procedencia.procedencia_id);
        $("#cboServicio").val(json.oMic_servicio.servicio_id);
        //$("#cboExamen").val(json.oMic_examen.examen_id);

        $("#cboMedico").val(json.oMic_medico.medico_id);
        $("#txtComentAdicional").val(json.orden_comentarios);
        $("#txtCodigoBarras").prop("disabled", true);
    } else {
        $("#txtOrdenId").val("");
        $('.cl_ocultar_nuevo').hide();
        $("#form").each(function () {
            $("#txtFechaOrden").prop('disabled', false);
            $("#txtNumeroOrden").prop('disabled', false);
            $("#txtCodigoBarras").prop("disabled", true);
            this.reset();
        });
        //se adiciona para manuaes
        var d = new Date();
        var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
        $("#txtFechaOrden").val(fecha_actual);
        $("#txtNumeroOrden").val('AUTOGEN');

        $("#txtFechaOrden").prop('disabled', true);
        $("#txtNumeroOrden").prop('disabled', true);
        
    }
    $('#FormModal').modal('show');
}


function abrirPopUpForm_det(json) {
    if (json != null) {
        $('#FormModal_orden_examenes').modal('show');
        $("#txtOrdenExamen_orden_id").val(json.orden_id);
        $("#txtOrdenExamen_orden_desc").val(json.orden_numero + " - " + json.orden_fecha + " | " + json.oMic_persona.persona_apellidos + ", " + json.oMic_persona.persona_nombres);
        _Obtener_Mic_orden_detalle_examen(json.orden_id);
    } 
}


function _ObtenerIDPersona(HC) {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerHC + "?HC=" + HC,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data.length != 0) {
                $("#txtApellidos").val(data.data[0].persona_apellidos);
                $("#txtNombres").val(data.data[0].persona_nombres);
                $("#txtFechaNac").val(data.data[0].persona_fecha_nac);
                $("#cboGenero").val(data.data[0].persona_genero);
                $("#txtEdad").val(window._calcEdad(data.data[0].persona_fecha_nac));
            } else {
                swal("Mensaje", "No existe paciente con HC " + HC+", complete los datos", "warning")
            }
        },
        error: function (error) {
            console.log(error);
            location.reload();
        },
        beforeSend: function () {
        },
    });
}

function cboMuetsraEXA(Exa, selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_muestra_examenEXA + "?EXA=" + Exa,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboTipoMuestra").html("");
            $("#cboTipoMuestraNivel2").html("");
            $("#grupoTipoMuestraNivel2").hide();
            muestrasExamenActual = (data.data || []).map(function (item) { return item.oMic_muestra; });
            var niveles1 = muestrasExamenActual.filter(function (item) { return !item.muestra_padre_id; });
            $.each(niveles1, function (i, item) {
                $("<option>").attr({ "value": item.muestra_id }).text(item.muestra_desc).appendTo("#cboTipoMuestra");
            });
            if (selectec) {
                var seleccionada = muestrasExamenActual.find(function (item) { return item.muestra_id === selectec; });
                if (seleccionada && seleccionada.muestra_padre_id) {
                    $("#cboTipoMuestra").val(seleccionada.muestra_padre_id);
                    actualizarTipoMuestraNivel2(seleccionada.muestra_id);
                } else {
                    $("#cboTipoMuestra").val(selectec);
                    actualizarTipoMuestraNivel2(null);
                }
            } else {
                $("#cboTipoMuestra").val($("#cboTipoMuestra option:first").val());
                actualizarTipoMuestraNivel2(null);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}

function actualizarTipoMuestraNivel2(selectec) {
    var padreId = $("#cboTipoMuestra").val();
    var hijos = muestrasExamenActual.filter(function (item) { return item.muestra_padre_id === padreId; });
    $("#cboTipoMuestraNivel2").html("");
    if (hijos.length === 0) {
        $("#grupoTipoMuestraNivel2").hide();
        $("#cboTipoMuestraNivel2").prop("required", false);
        return;
    }
    $.each(hijos, function (i, item) {
        $("<option>").attr({ "value": item.muestra_id }).text(item.muestra_desc).appendTo("#cboTipoMuestraNivel2");
    });
    $("#grupoTipoMuestraNivel2").show();
    $("#cboTipoMuestraNivel2").prop("required", true);
    $("#cboTipoMuestraNivel2").val(selectec || $("#cboTipoMuestraNivel2 option:first").val());
}

function tipoMuestraTerminalSeleccionada() {
    if ($("#grupoTipoMuestraNivel2").is(":visible")) return $("#cboTipoMuestraNivel2").val();
    return $("#cboTipoMuestra").val();
}


function Guardar(estadoModal) {
    if ($("#form").valid()) {
        var request = {
            objeto: {
                orden_id: $("#txtOrdenId").val(),
                oMic_persona: {
                    persona_hc: $("#txtHC").val(),
                    persona_apellidos: $("#txtApellidos").val(),
                    persona_nombres: $("#txtNombres").val(),
                    persona_fecha_nac: $("#txtFechaNac").val(),
                    persona_genero: $("#cboGenero").val()
                },
                orden_fecha: $("#txtFechaOrden").val(),
                orden_numero: $("#txtNumeroOrden").val(),
                orden_estado: ($("#cboEstado").val() == "1" ? true : false),
                orden_comentarios: $("#txtComentAdicional").val(),
                oMic_procedencia: { procedencia_id: $("#cboProcedencia").val() },
                oMic_servicio: { servicio_id: $("#cboServicio").val() },
                oMic_medico: { medico_id: $("#cboMedico").val() }
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_orden,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    if (estadoModal) {
                        $('#FormModal').modal('hide');
                    }
                    swal("Registro correcto", data.mensaje || "Paciente y orden guardados correctamente", "success")
                } else {
                    swal("No se pudo guardar", data.mensaje || "Revise los datos ingresados", "warning")
                }
            },
            error: function (error) {
                console.log(error);
                swal("No se pudo guardar", "No fue posible comunicarse con el servidor", "error")
            },
            beforeSend: function () {

            },
        });
    }
}

function Guardar_Siguiente() {
    Guardar(false);
    if (posicion_frame < posicion_frame_data.length - 1) {
        posicion_frame++;
        rec_abrirPopUpForm(posicion_frame);
    }
}


function _Obtener_Mic_orden_detalle_examen(orden_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._Obtener_Mic_orden_detalle_examen + "?orden_id=" + orden_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            //console.log(data);
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.oMic_examen.examen_codigo + '</td>';
                    html += '<td>' + item.oMic_examen.examen_desc + '</td>';

                    html += '<td>' + item.oMic_muestra.muestra_desc + (item.orden_det_muestra_comentarios == "" ? "" : " / "+item.orden_det_muestra_comentarios) +'</td>';

                    html += "<td>";
                    if (session_user_rol != 6) {
                        html += '<button class="btn btn-danger btn-sm ml-2" type="button" onclick=\'_EliminarMic_orden_detalle(' + JSON.stringify(item.orden_det_id) + ')\'><i class="fa fa-trash"></i></button>';
                    }
                    html += "</td>";

                    html += "<td>";
                    html += "<button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    //html += "<td><button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    //html += ' <button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_orden_detalle(' + item.orden_det_id + ')"><i class="fa fa-trash"></i></button>';
                    html += " <button class='btn btn-warning btn-sm ml-2' type='button' onclick='_RegistrarPrinterCodebarMic_orden_detalle(" + JSON.stringify(item.orden_det_id) + ")'><i class='fas fa-barcode'></i></button>";
                    html += "</td>";
                    html += '</tr>';
                });
                $("#tlbtbodyOrdenExamen").html(html);
            }
        },
        error: function (error) {
            console.log(error);
            //Actualizamos la página
            location.reload();
        },
        beforeSend: function () {
        },
    });
} 


function _RegistrarExaMuestraMic_orden_detalle() {
    if ($("#form_axamenes").valid()) {
        var muestraTerminal = tipoMuestraTerminalSeleccionada();
        if (!muestraTerminal) {
            swal("Muestra requerida", "Seleccione una opcion terminal de muestra", "warning");
            return;
        }
        var request = {
            objeto: {
                oMic_orden: { orden_id: $("#txtOrdenExamen_orden_id").val() },
                oMic_examen:{ examen_id: $("#cboExamen").val()},
                orden_det_codebar:$("#txtCodigoBarras").val(),
                orden_det_muestra_comentarios: $("#txComentariosMuestra").val(),
                oMic_muestra: { muestra_id: muestraTerminal},            
                fecha_muestra_toma:$("#txtFechaTomaMuestra").val(),
                fecha_muestra_recepcion:$("#txtFechaRecepcionMuestra").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._RegistrarExaMuestraMic_orden_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _Obtener_Mic_orden_detalle_examen($("#txtOrdenExamen_orden_id").val());
                    $('#FormModal_examenes').modal('hide');
                } else {
                    swal("No se pudo guardar", data.mensaje || "Revise el examen y la muestra", "warning")
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


function _EliminarMic_orden_detalle($orden_det_id) {
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
                url: $.MisUrls.url._EliminarMic_orden_detalle + "?orden_det_id=" + $orden_det_id,
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _Obtener_Mic_orden_detalle_examen($("#txtOrdenExamen_orden_id").val());
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



function _RegistrarPrinterCodebarMic_orden($orden_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea imprimir el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Sí",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",
        closeOnConfirm: true
    },

        function () {
            _AbrirCodigoBarras($.MisUrls.url._RegistrarPrinterCodebarMic_orden + "?orden_id=" + encodeURIComponent($orden_id) + "&orden_det_id=ALL&formato=html");
        });
}

function _RegistrarPrinterCodebarMic_orden_detalle($orden_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea imprimir el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Sí",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",
        closeOnConfirm: true
    },

        function () {
            _AbrirCodigoBarras($.MisUrls.url._RegistrarPrinterCodebarMic_orden + "?orden_id=0&orden_det_id=" + encodeURIComponent($orden_det_id) + "&formato=html");
        });
}

function _AbrirCodigoBarras(url) {
    var token = localStorage.getItem("muffin_token") || "";
    var popUpObj = window.open("", "CodigoBarrasMUFFIN", "toolbar=no,scrollbars=yes,location=yes,statusbar=no,menubar=no,resizable=yes,width=860,height=620,left=20,top=20");
    if (!popUpObj) {
        swal("Mensaje", "No se pudo abrir la ventana de etiquetas", "warning");
        return;
    }
    popUpObj.document.write("<!doctype html><html><head><meta charset='utf-8'><title>Etiquetas MUFFIN</title></head><body style='font-family:Arial,sans-serif;padding:24px;color:#294c52'>Generando etiquetas...</body></html>");
    popUpObj.document.close();
    fetch(url, { headers: token ? { "Authorization": "Bearer " + token } : {} })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("No se pudieron generar las etiquetas");
            }
            return response.text();
        })
        .then(function (html) {
            popUpObj.document.open();
            popUpObj.document.write(html);
            popUpObj.document.close();
            popUpObj.focus();
        })
        .catch(function (error) {
            popUpObj.document.open();
            popUpObj.document.write("<!doctype html><html><head><meta charset='utf-8'><title>Etiquetas MUFFIN</title></head><body style='font-family:Arial,sans-serif;padding:24px;color:#294c52'><strong>" + error.message + "</strong></body></html>");
            popUpObj.document.close();
        });
}
