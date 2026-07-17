var tabladata;
var posicion_frame = 0;
const posicion_frame_data = [];
var session_user_rol = $("#session_user_rol").val();

$(document).ready(function () {
    activarMenu("Mantenedor_resultado_micro");

    _Obtener_user_seccionMic_area_permiso($("#session_user_id").val(), "MICROBIOLOGIA");

    $("#btnGuardarCambios").click(function () {
        _GuardarMoMuestraMic_orden_detalle();
        _GuardarMic_orden_detalle_res(0, true);
        if ($("div#div_iden_atb").is(":visible")) {
            _GuardarMic_res_panel_detalle();
        }
    });


    $("#btnValPreliminar").click(function () {
        _GuardarMoMuestraMic_orden_detalle();
        _GuardarMic_orden_detalle_res(1, true);
        if ($("div#div_iden_atb").is(":visible")) {
            _GuardarMic_res_panel_detalle();
        }
    });
    $("#btnValPreliminar_siguiente").click(function () {
        _GuardarMoMuestraMic_orden_detalle();
        _GuardarMic_orden_detalle_res(1, false);
        if ($("div#div_iden_atb").is(":visible")) {
            _GuardarMic_res_panel_detalle();
        }
    });

    $("#btnValFinal").click(function () {
        _GuardarMoMuestraMic_orden_detalle();
        _GuardarMic_orden_detalle_res(2, true);
        if ($("div#div_iden_atb").is(":visible")) {
            _GuardarMic_res_panel_detalle();
        }
    });
    $("#btnValFinal_siguiente").click(function () {
        _GuardarMoMuestraMic_orden_detalle();
        _GuardarMic_orden_detalle_res(2, false);
        if ($("div#div_iden_atb").is(":visible")) {
            _GuardarMic_res_panel_detalle();
        }
    });

    $('#cboMicroOrganismos').change(function () {
        idSelec = $(this).val();
        cboMicroOrganismosCODEBARORGACOD($("#txtCodigoBarras").val(), idSelec);
    });


    $("#btnAddATB").click(function () {
        $("#formSeg").each(function () {
            this.reset();
        });
        $('#FormModalSeg').modal('show');
        cboObtenerMic_antibiotico();
    });
    $("#btnOPAdpanel").click(function () {
        $("#formTer").each(function () {
            this.reset();
        });
        $('#FormModalTer').modal('show');
        cboObtenerMic_orga();
        _ObtenerMic_orga_panel(0);
    });
    $("#btnAddPanelGuardar").click(function () {
        _RegistrarPanel();
    });

    $("#btnAddATBGuardar").click(function () {
        _GuardarManualPanel();
    });

    $("#btnAddComent").click(function () {
        $("#formComentDef").each(function () {
            this.reset();
        });
        $('#FormModalComent').modal('show');
        cboObtenerMic_res_comentarios_def();
    });

    $("#btnAddComentarioDefinido").click(function () {
        valor_selecionado = $("#cboComentarioDef option:selected").text();
        valor_actual = $("#IDEN_COMENT").val();

        //console.log(valor_selecionado + "\n" + valor_actual);
        //new_coment += valor_selecionado + "\n" + valor_actual; 
        $("#IDEN_COMENT").val(valor_actual + "\n" + valor_selecionado);
        $('#FormModalComent').modal('hide');
    });


    var d = new Date();
    var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");

    var f = new Date();
    f.setDate(f.getDate() - 10);

    var fecha_15 = f.getFullYear() + "-" + (f.getMonth() + 1).toString().padStart(2, "0") + "-" + f.getDate().toString().padStart(2, "0");

    $("#txtfechaInicio").val(fecha_15);
    $("#txtfechaFin").val(fecha_actual);

    listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val(), '', $("#cboFiltro").val(), $("#session_user_id").val())
    $("#btnBuscar").click(function () {
        var table = $('#tbdata').DataTable();
        table.destroy();
        listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val(), $("#cboArea").val(), $("#cboFiltro").val(), $("#session_user_id").val())
    });

    $("#txtBuscar").keypress(function (e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code == 13) {
            var table = $('#tbdata').DataTable();
            table.destroy();
            listarRistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val(), $("#cboArea").val(), $("#cboFiltro").val(), $("#session_user_id").val())
        }
    });


    $('#cboFiltro').change(function () {
        cboFiltro = $(this).val();
        if (cboFiltro == 'Instrumento') {
            $('#thTlbOrdenColumFecha').html('Proceso Inst. Fecha');
        } else {
            $('#thTlbOrdenColumFecha').html('Órden Fecha');
        }
        
    });

    $("#btnDeletePanel").click(function () {
        _EliminarMic_res_panel($("#IDEN_PANEL_ID").val());
    });

    $("#btnOPEnviarVitek").click(function () {
        _RegistrarEnviarInstrumentoMic_orden_detalle($("#txtIdOrdenDet").val());
    });

    $("#btnOPDeleteEventos").click(function () {
        _RegistrarDeleteEventosMic_orden_detalle($("#txtIdOrdenDet").val());
    });
    $("#btnOPReportarEmail").click(function () {
        _RegistrarEnviarAlarmaEmailMic_orden_detalle($("#txtIdOrdenDet").val());
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
        if (posicion_frame < posicion_frame_data.length - 1) {
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

    //OBTENER RECUENTO EN PANEL +
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_res_panel_recuento,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#IDEN_RECUENTO").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.panel_res_recuento_desc }).text(item.panel_res_recuento_desc).appendTo("#IDEN_RECUENTO");
                })
                $("#IDEN_RECUENTO").val($("#IDEN_RECUENTO option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });

    $("#btnComentariosMuestra").click(function () {
        _ObtenerSecuenciaMic_seccion($("#txtExamenIdCarga").val());//txComentariosMuestra
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
function listarRistros(orden_fecha_ini, orden_fecha_fin, orden_buscar, orden_area, orden_filtro, orden_usuario) {
    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._Obtener_resMic_orden_detalle + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&orden_buscar=" + orden_buscar + "&orden_area=" + orden_area + "&orden_filtro=" + orden_filtro + "&orden_usuario=" + orden_usuario,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "oMic_orden", render: function (data) { return data.orden_fecha; } },
            { "data": "oMic_orden", render: function (data) { return data.orden_numero; } },

            { "data": "oMic_orden", render: function (data) { return data.oMic_persona["persona_hc"]; } },
            { "data": "oMic_orden", render: function (data) { return data.oMic_persona["persona_apellidos"] + ", " + data.oMic_persona["persona_nombres"]; } },

            { "data": "oMic_examen", render: function (data) { return data.examen_desc } },

            { "data": "oMic_orden", render: function (data) { return data.oMic_procedencia["procedencia_desc"]; } },
            { "data": "oMic_orden", render: function (data) { return data.oMic_servicio["servicio_desc"]; } },


            {
                "data": "orden_det_id", "render": function (data, type, row, meta) {

                    posicion_frame_data[meta.row] = (JSON.stringify(row));

                    btn_rev = "<button class='btn btn-primary btn-sm' type='button' onclick='rec_abrirPopUpForm_ini(" + row.orden_det_id + ")'><i class='fa fa-user-plus'></i></button>"
                        + " <button class='btn btn-warning btn-sm' type='button' onclick='_RegistrarPrinterCodebarMic_orden(" + row.orden_det_id + ")'><i class='fas fa-barcode'></i></button> ";
                    if (session_user_rol == "4" || session_user_rol == "5" || session_user_rol == "6" || session_user_rol == "7") {
                        btn_rev = "";
                    }

                    return btn_rev +
                        (row.orden_det_muestra_recepcion_estado == false ? "" : " <span class='badge badge-success'><i class='fa fa-vials'></i></span>") +
                        (row.fecha_proc_resultado == "" ? "" : " <span class='badge badge-primary'>GU</span>") +
                        (row.fecha_proc_preliminar == "" ? "" : " <span class='badge badge-warning'>VP</span>") +
                        (row.fecha_proc_final == "" ? "" : " <span class='badge badge-success'>VF</span>") +
                        (row.fecha_proc_preliminar == "" ? "" : " <button class='btn btn-info btn-sm' type='button' onclick='_DocumentoPDFMic_temp(" + row.oMic_orden.orden_id + ")'><i class='fa fa-download'></i></button>")
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
    });//});
}


function rec_abrirPopUpForm_ini(orden_det_id) {
    if (orden_det_id) {
        for (k = 0; k < posicion_frame_data.length; k++) {
            var json = JSON.parse(posicion_frame_data[k]);
            if (json.orden_det_id == orden_det_id) {
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

function revisa_boton_validar() {
    $("#btnValPreliminar").hide();
    $("#btnValPreliminar_siguiente").hide();

    $("#btnValFinal").hide();
    $("#btnValFinal_siguiente").hide();

    session_user_rol_validacion_preliminar = $("#session_user_rol_validacion_preliminar").val() == "True"?1:0;
    session_user_rol_validacion_final = $("#session_user_rol_validacion_final").val() == "True" ? 1 : 0;

    if (session_user_rol_validacion_preliminar == 1) {
        $("#btnValPreliminar").show();
        $("#btnValPreliminar_siguiente").show();
    }
    if (session_user_rol_validacion_final == 1) {
        $("#btnValFinal").show();
        $("#btnValFinal_siguiente").show();
    }
    
}

function abrirPopUpForm(json) {
    revisa_boton_validar();

    $("#divListaParama").html('<p style="text-align: center"><i class="fa fa-spin fa-spinner fa-5x"></i></p>');
    $("#form").each(function () {
        this.reset();
    });
    $("#IDEN_PANEL_ID").val("");
    $("#IDEN_ORGA_ID").val("");
    $("#IDEN_ORGA").val("");
    $("#IDEN_RECUENTO").val("");
    $("#IDEN_FENO").val("");
    $("#IDEN_COMENT").val("");
    $("#tlbtbody_atb").html("");

    if (json != null) {
        $("#txtIdOrdenDet").val(json.orden_det_id);
        $("#h6TitleCard").html(json.oMic_orden.oMic_persona.persona_hc + " - " + json.oMic_orden.oMic_persona.persona_apellidos + " " + json.oMic_orden.oMic_persona.persona_nombres + " | " + json.oMic_examen.examen_desc + " | " + json.oMic_orden.orden_fecha + "  (" + json.oMic_orden.orden_numero + ")");
        $("#lblEdad").html(json.oMic_orden.oMic_persona.persona_edad + " / " + (json.oMic_orden.oMic_persona.persona_genero == "M" ? "Masculino" : "Femenino"));
        $("#lblComentOrden").html(json.oMic_orden.orden_comentarios);
        $("#lblmedico").html(json.oMic_orden.oMic_medico.medico_apellidos + ' ' + json.oMic_orden.oMic_medico.medico_nombres);
        $("#lblProcedencia").html(json.oMic_orden.oMic_procedencia.procedencia_desc);
        $("#lblServicio").html(json.oMic_orden.oMic_servicio.servicio_desc);
        $("#lblExamen").html(json.oMic_examen.examen_desc);

        $("#txtExamenEnviarInstrumento").val(json.oMic_examen.examen_analizador_send);
        $("#txtExamenRecuento").val(json.oMic_examen.examen_recuento);
        if (json.oMic_examen.examen_recuento == 1) {//SE VISUALIZA RECUENTO
            $("#divRecuentoColonias").show();
        } else {
            $("#divRecuentoColonias").hide();
        }

        if (json.oMic_examen.examen_analizador_send == 1) {//SE VISUALIZA ENVIO AL INSTRUMENTO Y PANEL
            $("#btnOPEnviarVitek").show();
            $("#btnOPAdpanel").show();
        } else {
            $("#btnOPEnviarVitek").hide();
            $("#btnOPAdpanel").hide();
        }

        _ObtenerMic_orden_detalle_examen_muestra(json.orden_det_id);

        param_ObtenerOrdenIdMic_orden_detalle_res(json.orden_det_id);
        cboMicroOrganismosCODEBAR(json.orden_det_codebar);
    } else {
        $("#form").each(function () {
            this.reset();
        });
        $("#IDEN_PANEL_ID").val("");
        $("#IDEN_ORGA_ID").val("");
        $("#IDEN_ORGA").val("");
        $("#IDEN_RECUENTO").val("");
        $("#IDEN_FENO").val("");
        $("#IDEN_COMENT").val("");
        $("#tlbtbody_atb").html("");
    }
    $('#FormModal').modal('show');
}

function _ObtenerMic_orden_detalle_examen_muestra(orden_det_id) {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orden_detalle_examen_muestra + "?orden_det_id=" + orden_det_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("#txtCodigoBarras").val(item.orden_det_codebar);
                    $("#txComentariosMuestra").val(item.orden_det_muestra_comentarios);
                    cboMuetsraEXA(item.oMic_examen.examen_id, item.oMic_muestra.muestra_cod_alfa);
                    $("#txtExamenIdCarga").val(item.oMic_examen.examen_id);//version new
                    $("#cboTipoLocalizacion").val(item.oMic_orden.orden_tipo_loc);
                    $("#txtFechaTomaMuestra").val(item.fecha_muestra_toma);
                    $("#txtFechaRecepcionMuestra").val(item.fecha_muestra_recepcion);
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


function cboMuetsraEXA(Exa, selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_muestra_examenEXA + "?EXA=" + Exa,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboTipoMuestra").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.oMic_muestra.muestra_cod_alfa }).text(item.oMic_muestra.muestra_desc).appendTo("#cboTipoMuestra");
                })
                $("#cboTipoMuestra").val(selectec);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}

function param_ObtenerOrdenIdMic_orden_detalle_res(orden_det_id) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerOrdenIdMic_orden_detalle_res + "?orden_det_id=" + orden_det_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            //$("#divListaParama").html("");
            html = '<h6 class="card-title mb-0 text-info">Resultado Parámetros</h6>';
            if (data.data != null) {
                //PRIMER RECOGIDO GENERA LOS CONTROLES
                $.each(data.data, function (i, item) {
                    html += item.param_html;
                });
                $("#divListaParama").html(html);

                //SEGUNDO RECOGIDO COMPLETA DATOS
                $.each(data.data, function (i, item) {
                    switch (item.param_tipo) {
                        case 'COMBO_BOX':
                            $("#" + item.param_cod).val(item.param_value1);
                            break;

                        case 'TEXT_AREA':
                            $("#" + item.param_cod).val(item.param_value1);
                            break;

                        case 'TEXT':
                            $("#" + item.param_cod).val(item.param_value1);
                            break;

                        default:
                            break;
                    }
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

function cboMicroOrganismosCODEBAR(codebar) {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerCodebarMic_res_panel + "?codebar=" + codebar,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboMicroOrganismos").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.respanel_organismo_cod }).text(item.respanel_organismo_desc).appendTo("#cboMicroOrganismos");
                })
                $("#cboMicroOrganismos").val($("#cboMicroOrganismos option:first").val());
                cboMicroOrganismosCODEBARORGACOD(codebar, $("#cboMicroOrganismos option:first").val());
            }
            if (data.data.length == 0) {
                //$('#div_iden_atb').hide();
            }
        },
        error: function (error) {
            console.log(error)
            if (error.abort.name == "abort") {
                window.location.href = $.MisUrls.url._IndexLogin;
            }
        },
        beforeSend: function () {
        },
    });
}

function cboMicroOrganismosCODEBARORGACOD(codebar, organismo_cod) {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerCodebarOrgacodMic_res_panel + "?codebar=" + codebar + "&organismo_cod=" + organismo_cod,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data.length != 0) {
                $('#div_iden_atb').show();
                $('#div_modal_modal_dialog_1').removeClass("modal-lg").addClass("modal-xl");
                $('#div_col_sm_mitad_pri').removeClass("col-sm-12").addClass("col-sm-6");
                $('#div_iden_atb').removeClass("col-sm-0").addClass("col-sm-6");

                $("#IDEN_PANEL_ID").val(data.data[0].respanel_id);
                $("#IDEN_ORGA_ID").val(data.data[0].respanel_organismo_cod);
                $("#IDEN_RECUENTO").val(data.data[0].respanel_recuento);
                $("#IDEN_ORGA").val(data.data[0].respanel_organismo_desc);
                $("#IDEN_FENO").val(data.data[0].respanel_organismo_fenotipo);
                $("#IDEN_COMENT").val(data.data[0].respanel_organismo_comentario);
                tlb_ObtenerCodebarOrgaCod_lista_atb(codebar, organismo_cod);
            }
            if (data.data.length == 0) {//NO EXISTE IDEN /AST
                $('#div_iden_atb').hide();
                $('#div_modal_modal_dialog_1').removeClass("modal-xl").addClass("modal-lg");
                $('#div_col_sm_mitad_pri').removeClass("col-sm-6").addClass("col-sm-12");
                $('#div_iden_atb').removeClass("col-sm-6").addClass("col-sm-0");

            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}



function tlb_ObtenerCodebarOrgaCod_lista_atb(codebar, organismo_cod) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerCodebarOrgaCodMic_res_panel_detalle + "?codebar=" + codebar + "&organismo_cod=" + organismo_cod,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#tlbtbody_atb").html("");
            html = '';
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    color_table_fila = " class='table-success'";
                    mecan_table_fila = "";
                    if (item.respaneldet_anti_macanismo == 1) {
                        mecan_table_fila = " style='font-weight: bold;' ";
                    }
                    if (item.respaneldet_anti_inter == "I") {
                        color_table_fila = " class='table-warning'";
                    }
                    if (item.respaneldet_anti_inter == "R" || item.respaneldet_anti_inter == "+") {
                        color_table_fila = " class='table-danger'";
                    }
                    html += "<tr" + color_table_fila + mecan_table_fila + ">" +
                        "<td><input type='hidden' value='" + item.respaneldet_anti_cod + "'/>" + item.respaneldet_anti_desc + "</td>" +
                        "<td><input class='form-control form-control-sm model' type='text' value='" + item.respaneldet_anti_cmi + "'></td>" +
                        "<td>" +
                        "<select class='form-control form-control-sm model clInter'>" +
                        "<option val='S' " + (item.respaneldet_anti_inter == 'S' ? 'selected' : '') + ">S</option>" +
                        "<option val='SDD' " + (item.respaneldet_anti_inter == 'SDD' ? 'selected' : '') + ">SDD</option>" +
                        "<option val='I' " + (item.respaneldet_anti_inter == 'I' ? 'selected' : '') + ">I</option>" +
                        "<option val='R' " + (item.respaneldet_anti_inter == 'R' ? 'selected' : '') + ">R</option>" +
                        "<option val='+' " + (item.respaneldet_anti_inter == '+' ? 'selected' : '') + ">+</option>" +
                        "<option val='-' " + (item.respaneldet_anti_inter == '-' ? 'selected' : '') + ">-</option>" +
                        "</select>" +
                        "</td>" +
                        "<td class='td_center'><input type='checkbox' " + (item.respaneldet_anti_estado == true ? "checked" : "") + "></td>" +
                        "<td>" +
                        "<select class='form-control form-control-sm model clMetodol'>" +
                        "<option val='CMI' " + (item.respaneldet_anti_metodologia == 'CMI' ? 'selected' : '') + ">CMI</option>" +
                        "<option val='DISCO' " + (item.respaneldet_anti_metodologia == 'DISCO' ? 'selected' : '') + ">DISCO</option>" +
                        "</select>" +
                        "</td>" +
                        "</tr>";

                })
                $("#tlbtbody_atb").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}


function _GuardarMic_orden_detalle_res(tipo, estadoModal) {
    columnas_id = "";
    columnas_val = "";
    $('#divListaParama').find('input, select, button,textarea').each(function () {
        columnas_val += ($(this).val()) + "|";
        columnas_id += ($(this).attr('id')) + "|";
    });
    var request = {
        objeto: {
            orden_det_id: $("#txtIdOrdenDet").val(),
            temporal1: columnas_id,
            temporal2: columnas_val,
            other1: tipo,
            other2: $("#session_user_id").val()
        }
    }
    if ($("#form").valid()) {
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_orden_detalle_res,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    if (estadoModal) {
                        $('#FormModal').modal('hide');
                    } else {
                        if (posicion_frame < posicion_frame_data.length - 1) {
                            posicion_frame++;
                            rec_abrirPopUpForm(posicion_frame);
                        }
                    }
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


function _GuardarMoMuestraMic_orden_detalle() {
    if ($("#form").valid()) {
        var request = {
            objeto: {
                orden_det_id: $("#txtIdOrdenDet").val(),
                orden_det_codebar: $("#txtCodigoBarras").val(),

                orden_det_temp1: $("#cboTipoLocalizacion").val(),

                orden_det_muestra_comentarios: $("#txComentariosMuestra").val(),
                oMic_muestra: { muestra_cod_alfa: $("#cboTipoMuestra").val() },
                fecha_muestra_toma: $("#txtFechaTomaMuestra").val(),
                fecha_muestra_recepcion: $("#txtFechaRecepcionMuestra").val()
            }
        }
        //console.log(request);
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMoMuestraMic_orden_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    //tabladata.ajax.reload();
                    //$('#FormModal').modal('hide');
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


function _GuardarMic_res_panel_detalle() {
    orden_det_id = $("#txtIdOrdenDet").val(),
    orga_panel_id = $("#IDEN_PANEL_ID").val();
    orga_id = $("#IDEN_ORGA_ID").val();
    orga_recuento = $("#IDEN_RECUENTO").val();
    orga_feno = $("#IDEN_FENO").val();
    orga_coment = $("#IDEN_COMENT").val();

    columnas_cod_atb = "";
    columnas_cmi = "";
    columnas_inter = "";
    columnas_estado = "";
    columnas_metodologia = "";


    $('tbody#tlbtbody_atb').find('input:checkbox').each(function () {
        columnas_estado += ($(this).prop('checked')) + "|";
    });
    $('tbody#tlbtbody_atb').find('select.clInter').each(function () {
        columnas_inter += ($(this).val()) + "|";
    });
    $('tbody#tlbtbody_atb').find('input:text').each(function () {
        columnas_cmi += ($(this).val()) + "|";
    });
    $('tbody#tlbtbody_atb').find('input:hidden').each(function () {
        columnas_cod_atb += ($(this).val()) + "|";
    });
    $('tbody#tlbtbody_atb').find('select.clMetodol').each(function () {
        columnas_metodologia += ($(this).val()) + "|";
    });

    if ($("#form").valid()) {//&& respaneldet_anti_cmi_all!=""
        var request = {
            objeto: {
                oMic_res_panel: {
                    oMic_orden_detalle: { orden_det_id: orden_det_id },
                    respanel_id: orga_panel_id,
                    respanel_organismo_cod: orga_id,
                    respanel_recuento: orga_recuento,
                    respanel_organismo_comentario: orga_coment,
                    respanel_organismo_fenotipo: orga_feno
                },
                respaneldet_anti_cod_all: columnas_cod_atb,
                respaneldet_anti_cmi_all: columnas_cmi,
                respaneldet_anti_inter_all: columnas_inter,
                respaneldet_anti_estado_all: columnas_estado,
                respaneldet_anti_metodologia_all: columnas_metodologia
            }
        };

        console.log(request);

        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_res_panel_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
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

function cboObtenerMic_res_comentarios_def() {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_res_comentarios_def,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                $("#cboComentarioDef").html("");
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.rescomen_cod }).text(item.rescomen_desc).appendTo("#cboComentarioDef");
                })
                $("#cboComentarioDef").val($("#cboComentarioDef option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}

function cboObtenerMic_orga() {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orga,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                $("#cboOrgaLista").html("");
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.orga_id }).text(item.orga_desc).appendTo("#cboOrgaLista");
                })
                $("#cboOrgaLista").val($("#cboOrgaLista option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}

function cboObtenerMic_antibiotico() {
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_antibiotico,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboATBNombre").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.atb_id }).text(item.atb_desc).appendTo("#cboATBNombre");
                })
                $("#cboATBNombre").val($("#cboATBNombre option:first").val());
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}



function _RegistrarPanel() {
    if ($("#formTer").valid()) {
        var request = {
            objeto: {
                respanel_codebar: $("#txtCodigoBarras").val(),
                temporal1: $("#cboPanelLista").val(),
                respanel_organismo_cod: $("#cboOrgaLista").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._RegistrarMic_res_panel,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    $('#FormModalTer').modal('hide');
                    cboMicroOrganismosCODEBAR($("#txtCodigoBarras").val());
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

function _GuardarManualPanel() {
    if ($("#formTer").valid()) {
        var request = {
            objeto: {
                oMic_res_panel: {
                    respanel_id: $("#txtCodigoBarras").val() + "_" + $("#IDEN_ORGA_ID").val()
                },
                respaneldet_anti_cod: $("#cboATBNombre").val(),
                respaneldet_anti_cmi: $("#txtATBCmi").val(),
                respaneldet_anti_inter: $("#cboATBInter").val()
            }
        }

        jQuery.ajax({
            url: $.MisUrls.url._GuardarManualMic_res_panel_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    $('#FormModalSeg').modal('hide');
                    cboMicroOrganismosCODEBAR($("#txtCodigoBarras").val());
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

function _DocumentoPDFMic_temp(orden_id) {

    //var url = $.MisUrls.url._DocumentoPDFMic_temp + "?IdMic_orden_detalle=" + id;
    //window.open(url);

    //OBTENER 
    var url = $.MisUrls.url._Download_res_es_Trans_pdf + "?orden_id=" + orden_id;
    //$(location).attr('href', url);
    //window.open(url);

    popUpObj = window.open(url,
        "ModalPopUp",
        "fullscreen = yes," +
        "toolbar=no," +
        "scrollbars=no," +
        "location=yes," +
        "statusbar=no," +
        "menubar=no," +
        "resizable=yes," +
        "width=800," +
        "height=400," +
        "left = 0," +
        "top= 0"
    );
    popUpObj.focus();
    LoadModalDiv();
}



function _EliminarMic_res_panel($respanel_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea eliminar el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },

        function () {
            jQuery.ajax({
                url: $.MisUrls.url._EliminarMic_res_panel + "?respanel_id=" + $respanel_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        cboMicroOrganismosCODEBAR($("#txtCodigoBarras").val());
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



function _Obtener_user_seccionMic_area_permiso(usuario_id, area_seccion) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._Obtener_user_seccionMic_area_permiso + "?usuario_id=" + usuario_id + "&area_seccion=" + area_seccion,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboArea").html("");
            if (data.data != null) {
                var cantidad = 0;
                $.each(data.data, function (i, item) {
                    //if (cantidad == 0) {
                    //    $("<option>").attr({ "value": "ALL" }).text("[ TODOS ]").appendTo("#cboArea");
                    //}
                    $("<option>").attr({ "value": item.oMic_area.area_id }).text(item.oMic_area.area_desc).appendTo("#cboArea");
                    cantidad++;
                })

                if (cantidad == 0) {
                    $("<option>").attr({ "value": "0" }).text("[ USUARIO SIN PERMISOS ASIGNADOS ]").appendTo("#cboArea");
                }
                $("#cboArea option:first").val();
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}


function _RegistrarEnviarInstrumentoMic_orden_detalle($orden_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea enviar al Intrumento la orden seleccionada?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },
        function () {
            jQuery.ajax({
                url: $.MisUrls.url._RegistrarEnviarInstrumentoMic_orden_detalle + "?orden_det_id=" + $orden_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        //console.log(data);
                    } else {
                        swal("Mensaje", "No se pudo resolver la operación", "warning")
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

function _RegistrarDeleteEventosMic_orden_detalle($orden_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea Eliminar los eventos de guardado y validación de la orden seleccionada?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },
        function () {
            jQuery.ajax({
                url: $.MisUrls.url._RegistrarDeleteEventosMic_orden_detalle + "?orden_det_id=" + $orden_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        tabladata.ajax.reload();
                    } else {
                        swal("Mensaje", "No se pudo resolver la operación", "warning")
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

function _RegistrarEnviarAlarmaEmailMic_orden_detalle($orden_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea reportar este resultado vía email al médico?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },
        function () {
            jQuery.ajax({
                url: $.MisUrls.url._RegistrarEnviarAlarmaEmailMic_orden_detalle + "?orden_det_id=" + $orden_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        tabladata.ajax.reload();
                    } else {
                        swal("Mensaje", "No se pudo resolver la operación", "warning")
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



function _ObtenerMic_orga_panel(selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orga_panel,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboPanelLista").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.orga_panel_id }).text(item.orga_panel_desc).appendTo("#cboPanelLista");
                })
                if (selectec == 0) {
                    $("#cboPanelLista option:first").val()
                } else {
                    $("#cboPanelLista").val(selectec);
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

function _RegistrarPrinterCodebarMic_orden($orden_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea imprimir el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",
        closeOnConfirm: true
    },

        function () {
            jQuery.ajax({
                url: $.MisUrls.url._RegistrarPrinterCodebarMic_orden + "?orden_id=" + 0 + "&orden_det_id=" + $orden_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        //_Obtener_Mic_orden_detalle_examen($("#txtOrdenExamen_orden_id").val());
                    } else {
                        swal("Mensaje", "No se pudo enviar a imprimir", "warning")
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
