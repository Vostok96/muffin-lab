$(document).ready(function () {
    activarMenu("Mantenedor_verificacion");
    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtFecha: "required"
        },
        messages: {
            txtFecha: "(*)"
        },
        errorElement: 'span'
    });

    $("#btnBuscar").click(function () {
        enter_temp_Verificar_orden_destinos();
        $("#txtBuscar").select();
    });

    $("#txtBuscar").keypress(function (e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code == 13) {
            enter_temp_Verificar_orden_destinos();
            $(this).select();
        }        
    });

    
});


function enter_temp_Verificar_orden_destinos() {
    var codebar = ($("#txtBuscarPrefijo").val()+""+$("#txtBuscar").val()).replace(/ /g, '');
    array_codebar = (codebar.replace("*", "@").replace("'", "@").replace(".", "@").replace("-", "@").replace("/", "@")).split('@');
    txt_codebar = array_codebar[0];
    
    txt_codebar_sufijo = "";
    if (array_codebar[1] != undefined) {
        _VerifcarMic_destinos_orden_detalle(txt_codebar, ($("#txtBuscarPrefijo").val()+""+$("#txtBuscar").val()));
        _ObtenerMic_orden_seach_destinoMic_orden(txt_codebar, ($("#txtBuscarPrefijo").val() + "" +$("#txtBuscar").val()));
    } else {
        _ObtenerMic_orden_seach_destinoMic_orden(txt_codebar, "ALL");
    }
}


function _ObtenerMic_orden_seach_destinoMic_orden(orden_numero, orden_det_codebar) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orden_seach_destinoMic_orden + "?orden_numero=" + orden_numero,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data.length >= 1) {
                $("#txtOrden_paciente_nombres").val(data.data[0].oMic_persona.persona_hc + " / " + data.data[0].oMic_persona.persona_apellidos + " " + data.data[0].oMic_persona.persona_nombres);
                $("#txtOrden_paciente_genero_edad").val((data.data[0].oMic_persona.persona_genero == "M" ? "Masculino" : "Femenino") + " / " + data.data[0].oMic_persona.persona_edad);

                $("#txtOrden_numero_fecha").val(data.data[0].orden_numero + " / " + data.data[0].orden_fecha);

                $("#txtOrden_medico").val(data.data[0].oMic_medico.medico_apellidos + " " + data.data[0].oMic_medico.medico_nombres);
                $("#txtOrden_procedencia").val(data.data[0].oMic_procedencia.procedencia_desc);
                $("#txtOrden_servicio").val(data.data[0].oMic_servicio.servicio_desc);
                $("#txtOrden_comentarios").val(data.data[0].orden_comentarios);

                $("#hiden_orden_id").val(data.data[0].orden_id);
                $("#hiden_orden_numero").val(data.data[0].orden_numero);
                $("#hiden_tipo_busqueda").val(data.data[0].orden_seach_busqueda_verificar);


                if (data.data[0].orden_seach_busqueda_verificar == "bus_codebar") {
                    _VerifcarMic_destinos_orden_detalle(data.data[0].orden_numero, orden_numero);
                }

                _ObtenerMic_destinos_orden_detalle(data.data[0].orden_id, data.data[0].orden_numero, orden_det_codebar);
                
            } else {
                $("#hiden_orden_id").val("");
                $("#hiden_orden_numero").val("");

                $("#txtOrden_paciente_nombres").val("");
                $("#txtOrden_paciente_genero_edad").val("");

                $("#txtOrden_numero_fecha").val("");

                $("#txtOrden_medico").val("");
                $("#txtOrden_procedencia").val("");
                $("#txtOrden_servicio").val("");
                $("#txtOrden_comentarios").val("");

                $("#divDetalleMuestras").html("");

                /*swal({
                    title: "Mensaje",
                    text: "La órden:" + orden_numero + " y Muestra:" + orden_det_codebar + " no encontrado.",
                    type: "danger",
                    showCancelButton: true,

                    confirmButtonText: "Si",
                    confirmButtonColor: "#DD6B55",

                    cancelButtonText: "Si",

                    closeOnConfirm: true
                });*/

                swal({
                    title: "Verificación de Muestra",
                    text: "La órden:" + orden_numero + " y Muestra:" + orden_det_codebar + " no encontrado.",
                    type: "error"
                });
            }
        },
        error: function (error) {
            console.log(error);
            //Reenvia la inicio;
            var url = $.MisUrls.url._IndexLogin;
            $(location).attr('href', url);
        },
        beforeSend: function () {
        },
    });
}


//int orden_id, string orden_numero, string orden_det_codebar
function _ObtenerMic_destinos_orden_detalle(orden_id, orden_numero, orden_det_codebar) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_destinos_orden_detalle + "?orden_id=" + orden_id + "&orden_numero=" + orden_numero + "&orden_det_codebar=" + orden_det_codebar,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                seach_t = '';

                html_table_header = '<div class="row"><div class="col-sm-12"><div class="table-responsive-sm">';
                html_table_header += '<table id="" class="table table-striped table-bordered nowrap table-sm" style="width:100%">';
                html_table_header += '<thead><tr><th>Acción</th><th># Orden</th><th>Destino</th><th>Fecha Destino</th><th>Responsable</th><th>Comentarios</th></tr></thead><tbody>';

                html_table_footer = '</tbody></table></div></div></div>';

                $.each(data.data, function (i, item) {
                    if (seach_t != item.oMic_orden_detalle.orden_det_codebar) {
                        if (seach_t != '') {
                            html += html_table_footer;
                        }
                        html += '<div class="row"><div class="col-sm-12"><h6 class="text-info">' + item.oMic_orden_detalle.orden_det_codebar + ' <span class="badge badge-info">' + item.oMic_orden_detalle.orden_det_codebar + '</span></h6></div></div>';
                        html += html_table_header;

                        seach_t = item.oMic_orden_detalle.orden_det_codebar;
                    }
                    if (seach_t != "") {
                        //html += '<tr><td>' + item.oMic_destinos_muestra.destinomues_orden + '</td><td>' + item.oMic_destinos_muestra.oMic_destinos.destinos_desc + '</td><td>' + item.destinosdet_fecha + '</td><td>' + item.destinosdet_user + '</td><td>' + item.destinosdet_comentarios +'</td></tr>';
                        html += '<tr>';
                        html += "<td><button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(item) + ")'><i class='fas fa-pen'></i></button>";
                        disabled_text = "disabled";
						
                        /*
						//aplica solo para HAMA
						if (item.oMic_destinos.destinos_orden_verificacion_requiere == '1') {
                            disabled_text = "";
                        }*/
                        html += " <button class='btn btn-danger btn-sm ml-2' type='button' onclick='_EliminarMic_destinos_orden_detalle(" + item.desti_orden_det_id + ")' " + disabled_text + "><i class='fa fa-trash'></i></button></td>";
                        html += '<td>' + item.oMic_destinos.destinos_orden_verificacion_orden + '</td><td>' + item.oMic_destinos.destinos_desc + '</td><td>' + item.desti_orden_det_fecha + '</td><td>' + item.desti_orden_det_user + '</td><td>' + item.desti_orden_det_comentarios + '</td>';
                        html += '</tr>';
                    }
                });

                if (html != '') {
                    html += html_table_footer;
                }
                $("#divDetalleMuestras").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
}


function abrirPopUpForm(json) {
    if (json != null) {
        $("#txtid").val(json.desti_orden_det_id);
        $("#txtDestino").val(json.oMic_destinos.destinos_desc);
        $("#txtFecha").val(json.desti_orden_det_fecha.replace(" ", "T"));
        $("#txtComentarios").val(json.desti_orden_det_comentarios);

        $("#hiden_orden_det_codebar").val(json.oMic_orden_detalle.orden_det_codebar);

        $("#txtFecha").prop("disabled", true);
    } else {
        $("#form").each(function () {
            this.reset();
            $("#txtid").val(0);
        });
    }
    $('#FormModal').modal('show');
}

function _GuardarMic_destinos_detalle() {
    if ($("#form").valid()) {
        var request = {
            objeto: {
                desti_orden_det_id: $("#txtid").val(),
                desti_orden_det_fecha: $("#txtFecha").val().replace("T", " "),
                desti_orden_det_comentarios: $("#txtComentarios").val(),
                desti_orden_det_user: $("#session_user_id").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_destinos_orden_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_destinos_orden_detalle($("#hiden_orden_id").val(), $("#hiden_orden_numero").val(), "ALL")
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



function _VerifcarMic_destinos_orden_detalle(orden_numero,orden_det_codebar) {
    swal({
        title: "Verificación de Muestra",
        text: "¿Desea verificar la órden:" + orden_numero + ", Muestra:" + orden_det_codebar + " ?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Si",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },

        function () {
            var request = {
                objeto: {                    
                    desti_orden_det_comentarios: "",
                    desti_orden_det_user: $("#session_user_id").val(),

                    oMic_orden_detalle: {
                        orden_det_codebar: orden_det_codebar,
                        oMic_orden: {
                            orden_id: $("#hiden_orden_id").val(),
                            orden_numero: $("#hiden_orden_numero").val()
                        }
                    },
                    oMic_destinos: {
                        destinos_tipo : "CODEBAR"
                    }
                }
            }

            jQuery.ajax({
                url: $.MisUrls.url._VerifcarMic_destinos_orden_detalle,
                type: "POST",
                data: JSON.stringify(request),
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_destinos_orden_detalle($("#hiden_orden_id").val(), orden_numero, orden_det_codebar)
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
        });
}


function _EliminarMic_destinos_orden_detalle($desti_orden_det_id) {
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
                url: $.MisUrls.url._EliminarMic_destinos_orden_detalle + "?desti_orden_det_id=" + $desti_orden_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_destinos_orden_detalle($("#hiden_orden_id").val(), $("#hiden_orden_numero").val(), "ALL")
                    } else {
                        swal("Mensaje", "No se pudo eliminar el registro", "warning")
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
