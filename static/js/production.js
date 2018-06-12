var typetimer
var typeinterval = 1000
var selID = ""
var val = ""

multipliers = {}

function getProduction(){
    $(".productionList").html("")
    $.getJSON("/internal/production/getProduction", function(data){
        $.each(data.production, function(k,v){
            var inputMaterials = "<table><tr>"
            maxproducable = []
            maxproducablebuild = []
            $.each(v, function(key,val){
                multipliers[data.toProduce[k].dbid] = data.toProduce[k].quantity
                clr = "green"
                if (val.stock >= (val.quantity * data.toProduce[k].quantity)){
                    stockquan = "<font color='"+clr+"'>"+val.stock+"/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducable.push(Math.floor(val.stock / (val.quantity * data.toProduce[k].quantity)))
                    producable = "<br>"+Math.floor(val.stock / (val.quantity * data.toProduce[k].quantity))
                }
                else{
                    clr = "red"
                    stockquan = "<font color='"+clr+"'>"+val.stock+"/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducable.push(0)
                    producable = ""
                }

                inprod = ""
                if (val.inbuild > 0){
                    stockquan = "<font color='"+clr+"'>"+val.stock+"(+"+val.inbuild+")/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducablebuild.push(Math.floor((val.stock + val.inbuild) / (val.quantity * data.toProduce[k].quantity)))
                }

                inputMaterials += "<td><img src='https://image.eveonline.com/Type/"+key+"_32.png'><br>"+data.translations[key].name + "<br>"+stockquan+""+producable+"</td>"
            })
            
            inputMaterials += "</tr></table>"
            $(".productionList").append("\
                                            <tr>\
                                            <td><input type='number' min=0 value='"+data.toProduce[k].quantity+"' id='dbid"+data.toProduce[k].dbid+"'></td>\
                                            <td><img src='https://image.eveonline.com/Type/"+k+"_32.png'><br>"+data.translations[k].name+"<br>"+Math.min(...maxproducable)+"("+Math.min(...maxproducablebuild)+")</td>\
                                            <td>"+inputMaterials+"</td>\
                                            </tr>\
            ")
        })
        $(":input[id^='dbid']").bind('keyup mouseup', function(){
            selID = (this.id).split("dbid")[1]
            val = $("#dbid"+selID).val()
            console.log(val)
            clearTimeout(typetimer);
            typetimer = setTimeout(function(){
                $.getJSON("/interal/production/setTarget/"+selID+"/"+val, function(){
                    getProduction()
                })
            }, typeinterval)
        })
    })
}

$(document).ready(function(){
    getProduction()
    
})