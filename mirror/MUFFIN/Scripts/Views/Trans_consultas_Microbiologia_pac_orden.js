
var tabladata;
var posicion_frame = 0;
const posicion_frame_data = [];
var session_user_rol = $("#session_user_rol").val();

$(document).ready(function () {   

    var d = new Date();
    var fecha_actual = d.getFullYear() + "-" + (d.getMonth() + 1).toString().padStart(2, "0") + "-" + d.getDate().toString().padStart(2, "0");
    
    var f = new Date();
    f.setDate(f.getDate() - 10);
    
    var fecha_15 = f.getFullYear() + "-" + (f.getMonth() + 1).toString().padStart(2, "0") + "-" + f.getDate().toString().padStart(2, "0");

    $("#txtfechaInicio").val(fecha_15);
    $("#txtfechaFin").val(fecha_actual);

    activarMenu("Mantenedor_consultas");
    
    listarRigistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
    $("#btnBuscar").click(function () {
        var table = $('#tbdata').DataTable();
        table.destroy();
        listarRigistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
    });

    $("#txtBuscar").keypress(function (e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code == 13) {
            var table = $('#tbdata').DataTable();
            table.destroy();
            listarRigistros($("#txtfechaInicio").val(), $("#txtfechaFin").val(), $("#txtBuscar").val())
        }
    });    
    //////////////////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////
})

function listarRigistros(orden_fecha_ini, orden_fecha_fin, orden_buscar) {
    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._Obtener_pac_ordenTrans_consultas + "?orden_fecha_ini=" + orden_fecha_ini + "&orden_fecha_fin=" + orden_fecha_fin + "&orden_buscar=" + orden_buscar,//orden_fecha_ini, orden_fecha_fin, orden_buscar
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "orden_fecha" },
            { "data": "orden_numero" },

            { "data": "oMic_persona", render: function (data) { return data.persona_hc } },
            { "data": "oMic_persona", render: function (data) { return data.persona_apellidos + ", " + data.persona_nombres} },

            { "data": "oMic_procedencia", render: function (data) { return data.procedencia_desc} },
            { "data": "oMic_servicio", render: function (data) { return data.servicio_desc } },
            { "data": "oMic_medico", render: function (data) { return (data.medico_apellidos + " " + data.medico_nombres).substring(0,20)+"..." } },

            {
                "data": "orden_temp1", "render": function (data) {
                    myArray_data = data.split("|");
                    myArrayrepetidos = {};
                    myArray_data.forEach(function (numero) {
                        myArrayrepetidos[numero] = (myArrayrepetidos[numero] || 0) + 1;
                    });
                    cadena_areas = '';
                    $.each(myArrayrepetidos, function (examen, cantidad) {
                        if (examen != "") {
                            cadena_areas += '<span class="badge badge-info">' + examen + ' (' + cantidad + ')</span> ';
                        }
                    });

                    return cadena_areas;
                }
            },
            { "data": "orden_temp2" },
            { "data": "orden_temp3" },
            { "data": "orden_temp4" },
            {
                "data": "orden_id", "render": function (data, type, row, meta) {
                    posicion_frame_data[meta.row] = (JSON.stringify(row));
                    pdf_des_es = " <button tile='Ver Detalle de Exámenes' class='btn btn-success btn-sm' type='button' onclick='abrirPopUpFormOrdenDet(" + JSON.stringify(row) + ")'><i class='fa fa-eye'></i></button>";

                    if (row.orden_temp3 > 0) {
                        pdf_des_es += " <button tile='Descargar resultados' class='btn btn-success btn-sm' type='button' onclick='_Download_res_es_Trans_pdf(" + row.orden_id + ")'><i class='fas fa-download'></i></button>";
                    }
                    return pdf_des_es;
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
    });
}

function _Download_res_es_Trans_pdf(orden_id) {
    //OBTENER 
    //var url = $.MisUrls.url._Download_res_es_Trans_pdf + "?orden_id=" + orden_id;
    //$(location).attr('href', url);
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

function abrirPopUpFormOrdenDet(json) {
    if (json != null) {
        $("#txtOrdenExamen_paciente").val(json.oMic_persona.persona_hc + " - " + json.oMic_persona.persona_apellidos + ", " + json.oMic_persona.persona_nombres);
        $("#txtOrdenExamen_SexoEdad").val(json.oMic_persona.persona_genero + " / " + json.oMic_persona.persona_edad);
        $("#txtOrdenExamen_orden").val(json.orden_numero + " / " + json.orden_fecha);
        $("#txtOrdenExamen_proc").val(json.oMic_procedencia.procedencia_desc);
        $("#txtOrdenExamen_servi").val(json.oMic_servicio.servicio_desc);
        $("#txtOrdenExamen_Comentarios").val(json.orden_comentarios);
        _Obtener_Mic_orden_detalle_examen(json.orden_id);
    } else {
        $("#form").each(function () {
            this.reset();
        });
    }
    $('#FormModal_orden_examenes').modal('show');
}


function _Obtener_Mic_orden_detalle_examen(orden_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._Obtener_Mic_orden_detalle_examen + "?orden_id=" + orden_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    orden_det_muestra_comentarios = "";
                    if (item.orden_det_muestra_comentarios != "") {
                        orden_det_muestra_comentarios = " / "+item.orden_det_muestra_comentarios;
                    }
                    html += '<tr>';
                    html += '<td>' + item.oMic_examen.examen_desc + '</td>';
                    html += '<td>' + item.oMic_muestra.muestra_desc + orden_det_muestra_comentarios + '</td>';
                    html += '<td>' + item.fecha_proc_resultado + '</td>';
                    html += '<td>' + item.fecha_proc_preliminar + '</td>';
                    html += '<td>' + item.fecha_proc_final + '</td>';
                    if (item.orden_det_descarga_pdf) {
                        html += '<td><i class="fa fa-check-circle" aria-hidden="true"></i></td>';
                    } else {
                        html += '<td></td>';
                    }

                    if (item.fecha_proc_preliminar != "") {
                        html += '<td>';
                        html += "<button tile='Ver resultado del examen' class='btn btn-success btn-sm' type='button' onclick='_ver_form_res(" + item.orden_det_id + ",`" + item.orden_det_codebar +"`)'><i class='fa fa-eye'></i></button>";
                        //html += "<button tile='Ver resultado del examen' class='btn btn-success btn-sm' type='button' onclick='_ver_form_res(" + item.orden_det_id + "," + item.orden_det_codebar+")'><i class='fa fa-eye'></i></button>";
                        //html += '<button tile="Ver resultado del examen" class="btn btn-success btn-sm" type="button" onclick="_ver_form_res()" ><i class="fa fa-eye"></i></button>';
                        //html += "('.$variable.','1')";
                        html += '</td>';
                    } else {
                        html += '<td></td>';
                    }
                    html += '</tr>';
                });
                $("#tlbtbodyOrdenExamen").html(html);
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


function _ver_form_res(orden_det_id, orden_det_codebar) {
    
    $("#form_det_orden_examen").each(function () {
        this.reset();
    });
    
    $("#txtOrdenExamenDet_paciente").val($("#txtOrdenExamen_paciente").val());
    $("#txtOrdenExamenDet_SexoEdad").val($("#txtOrdenExamen_SexoEdad").val());
    $("#txtOrdenExamenDet_orden").val($("#txtOrdenExamen_orden").val());
    $("#txtOrdenExamenDet_proc").val($("#txtOrdenExamen_proc").val());
    $("#txtOrdenExamenDet_servi").val($("#txtOrdenExamen_servi").val());
    $("#txtOrdenExamenDet_Comentarios").val($("#txtOrdenExamen_Comentarios").val());

    $('#FormModal_orden_examenes_det').modal('show');
    _ObtenerMic_orden_pdf_examen_paramMic_orden_detalle_res(orden_det_id, orden_det_codebar);
}


function _ObtenerMic_orden_pdf_examen_paramMic_orden_detalle_res(IdMic_orden_detalle, orden_det_codebar) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orden_pdf_examen_paramMic_orden_detalle_res + "?IdMic_orden_detalle=" + IdMic_orden_detalle,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            console.log(data);
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<b>' + item.param_desc + '</b>';
                    html += ': ' + (item.param_value1).replace('\n', '<br/>') + '<br/>';
                });
                $("#divOrdenExamenDetParam").html(html);

                //ORGANISMO
                console.log(orden_det_codebar);
                var xData_2 = $._ObtenerMic_orden_pdf_panel(orden_det_codebar);
                $("#divOrdenExamenDetIdenAst").html(xData_2);
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


$.extend({
    _ObtenerMic_orden_pdf_panel: function (orden_det_codebar) {
        var theResponse = null;
        // jQuery ajax
        $.ajax({
            url: $.MisUrls.url._ObtenerMic_orden_pdf_panel + "?orden_det_codebar=" + orden_det_codebar,
            type: "GET",
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            async: false,
            success: function (data) {
                html_param_exa = "";
                var cantidaOrga = 1;
                if (data.data != null) {
                    $.each(data.data, function (i, item) {
                        html_param_exa += "<tr><td colspan='2'><br><br></td></tr>";
                        html_param_exa += "<tr><td><b>Identificación #" + cantidaOrga + "</b></td><td><b>: </b>" + item.respanel_organismo_desc + "</td></tr>";

                        if (item.respanel_recuento != "") {
                            if (item.respanel_recuento != "-") {
                                html_param_exa += "<tr><td>Recuento de Colonias:</td><td>" + item.respanel_recuento + "</td></tr>";
                            }
                        }

                        var xData_3 = $._ObtenerMic_orden_pdf_panel_atb(item.respanel_id);

                        html_param_exa += "<tr><td colspan='2'>" + xData_3 + "</td></tr>";
                        if (item.respanel_organismo_fenotipo != "") {
                            html_param_exa += "<tr><td><b>Fenotipo</b></td><td><b>: </b>" + item.respanel_organismo_fenotipo + "</td></tr>";
                        }
                        if (item.respanel_organismo_comentario != "") {
                            html_param_exa += "<tr><td><b>Comentarios</b></td><td><b>: </b>" + item.respanel_organismo_comentario + "</td></tr>";
                        }
                        cantidaOrga++;
                    });
                }
                theResponse = html_param_exa;
            }
        });
        // Return the response text
        return theResponse;
    }
});


$.extend({
    _ObtenerMic_orden_pdf_panel_atb: function (respanel_id) {
        // local var
        var theResponse = null;
        // jQuery ajax
        $.ajax({
            url: $.MisUrls.url._ObtenerMic_orden_pdf_panel_atb + "?respanel_id=" + respanel_id,
            type: "GET",
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            async: false,
            success: function (data) {
                html_atb = "";
                if (data.data != null) {
                    if (data.data.length > 0) {
                        var arr_atb_fila1 = [];
                        var arr_atb_fila2 = [];

                        html_atb = "";
                        html_atb += "<table class='tlbAtb' style='border: 1px solid black;border-collapse: collapse;font-family:sans-serif; font-size:inherit; width:-webkit-fill-available;'><tr><td colspan='2' style='text-align: center; font-weight: bold;'>Información de Sensibilidad</td></tr>";
                        html_atb += "<tr>";

                        var contador = 1;
                        var filas = (data.data.length);
                        var columnas = (data.data.length) / 2;

                        var es_par = 0;
                        if (filas % 2 == 0) {
                            es_par = 0;
                        } else {
                            es_par = 1;
                        }

                        $.each(data.data, function (i, item) {
                            interpreta_inter = "";
                            if (item.respaneldet_anti_inter == "+") {
                                interpreta_inter = "(Positivo)";
                            }
                            if (item.respaneldet_anti_inter == "-") {
                                interpreta_inter = "(Negativo)";
                            }
                            if (item.respaneldet_anti_inter == "R") {
                                interpreta_inter = "(Resistente)";
                            }
                            if (item.respaneldet_anti_inter == "I") {
                                interpreta_inter = "(Intermedio)";
                            }
                            if (item.respaneldet_anti_inter == "S") {
                                interpreta_inter = "(Sensible)";
                            }

                            mecan_table_fila = "";
                            if (item.respaneldet_anti_macanismo == 1) {
                                mecan_table_fila = " style='font-weight: bold;'";
                            }

                            cmi_unidad = "";
                            if (item.respaneldet_anti_metodologia == "CIM" && item.respaneldet_anti_macanismo != 1) {
                                cmi_unidad = " <span style='font-size: smaller;'>μg/mL</span>";
                            }

                            if (contador <= (columnas + (es_par))) {//COLUMNA 1
                                arr_atb_fila1.push("<td" + mecan_table_fila + ">" + item.respaneldet_anti_desc + "</td><td" + mecan_table_fila + ">" + item.respaneldet_anti_cmi + cmi_unidad + "</td><td" + mecan_table_fila + ">" + interpreta_inter + "</td>");
                            } else {//COLUMNA 2
                                arr_atb_fila2.push("<td" + mecan_table_fila + ">" + item.respaneldet_anti_desc + "</td><td" + mecan_table_fila + ">" + item.respaneldet_anti_cmi + cmi_unidad + "</td><td" + mecan_table_fila + ">" + interpreta_inter + "</td>");
                            }
                            contador++;
                        });

                        if (es_par == 1) {
                            arr_atb_fila2.push("<td>-</td><td>-</td><td>-</td>");
                        }
                        //html_atb += html_atb_col_1 + "</table></td>" + html_atb_col_2 + "</table></td>";

                        html_atb_dos = "<td>";
                        html_atb_dos += "<table class='tlbAtb' style='border: 1px solid black;border-collapse: collapse;font-family: sans-serif;font-size: inherit;width: -webkit-fill-available;'>";
                        html_atb_dos += "<tr style='font-weight: bold;background-color: darkgray;'><td>Antibiótico</td><td>CMI</td><td>Interpretación</td><td> </td><td>Antibiótico</td><td>CMI</td><td>Interpretación</td></tr>";

                        html_atb += html_atb_dos;
                        for (let i = 0; i < arr_atb_fila1.length; i++) {
                            html_atb += "<tr>" + arr_atb_fila1[i] + "<td> </td>" + arr_atb_fila2[i] + "</tr>";
                        }
                        html_atb += "</table>";
                        html_atb += "</td>";

                        html_atb += "</tr>";
                        html_atb += "</table>";
                    }
                }
                theResponse = html_atb;
            }
        });
        // Return the response text
        return theResponse;
    }
});