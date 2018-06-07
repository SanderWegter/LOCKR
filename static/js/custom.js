function getRefresh(){
    $.getJSON("/internal/users/getRefreshingStatus", function(data){
        console.log(data)
        if (data.isRefreshing){
            $("#refreshSpinner").addClass("fa-spin")
        }
        else{
            $("#refreshSpinner").removeClass("fa-spin")
        }
    })
}
$(document).ready(function(){
    setInterval(function(){getRefresh()}, 5000)
})