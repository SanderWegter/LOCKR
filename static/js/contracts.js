function getContracts(){
    $.getJSON("/internal/contracts/getContracts", function(data){
        $.each(data.contracts, function(k,v){
            if (v.for_corporation == false){
                return 0
            }
            var d = new Date();
		    var curTime = d.getTime()
            var offset = d.getTimezoneOffset() * 60 * 1000;
            
            if (v.status === "finished"){
                stat = "success"
            }
            else{
                stat = "warning"
            }
            if (v.acceptor_id != 0){
                acceptee = data.translations[v.acceptor_id].name
            }
            else{
                acceptee = ""
            }

            $(".contractsList").append("\
                                        <tr class="+stat+">\
                                            <td>Issuer: "+data.translations[v.issuer_id].name+"<br><br>Title: "+v.title+"</td>\
                                            <td>"+acceptee+"</td>\
                                            <td>"+data.translations[v.start_location_id].name+"<br>"+data.translations[v.end_location_id].name+"</td>\
                                            <td>"+v.type+"</td>\
                                            <td>"+convertDate(v.date_issued-offset)+"<br>"+convertDate(v.date_completed-offset)+"</td>\
                                            <td>"+convertCurrency(v.price)+"</td>\
                                            <td>"+convertCurrency(v.reward)+"</td>\
                                        </tr>\
            ")
        })
    })
}

function convertDate(epoch) {
    var date = new Date(epoch)
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    var hours = ('0' + date.getHours()).slice(-2);
    var minutes = ('0' + date.getMinutes()).slice(-2);
    var seconds = ('0' + date.getSeconds()).slice(-2);
    return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds
}

function convertCurrency(amount) {
    if (amount >= 1000000 || amount <= -1000000) {
        if (amount >= 1000000000 || amount <= -1000000000) {
            amount = (amount / 1000000000).toFixed(3) + "B"
        } else {
            amount = (amount / 1000000).toFixed(3) + "M"
        }

    }
    return amount
}

$(document).ready(function(){
    getContracts()
})