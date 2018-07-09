var groups = ["Unknowns", "Members", "Leaders"]

function getUsers(){
    $.getJSON("/internal/character/getCharacters", function(data){
        $.each(data, function(k,v){
            var date = new Date( v.lastActive);
            var d = ( 
                (date.getMonth() + 1) + "/" +
                date.getDate() + "/" +
                date.getFullYear() + " " +
                date.getHours() + ":" +
                date.getMinutes() + ":" +
                date.getSeconds()
            );
            $(".userList").append(
                "<tr>\
                    <td><img class='img-circle' src='https://image.eveonline.com/Character/"+v.charID+"_64.jpg'><br>"+v.charName+"<br>"+v.charID+"</td>\
                    <td>"+v.groupName+"</td>\
                    <td>"+d+"</td>\
                    <td><a href='' onclick=\"editUserAdmin('" + v.charID + "', '"+v.groupName+"', '"+v.charName+"')\" data-toggle='modal' data-target='#editUserModalAdmin' class='btn btn-sm btn-info'>Edit</a></td>\
                </tr>"
            )
        })

    })
}

function editUserAdmin(charID, group, charName){
    $("#group").html("")
    $("#charName").val(charName)
    $("#charID").val(charID)
    $("#group").append("<option value='"+group+"'>"+group+"</option>")
    $.each(groups, function(k,v){
        if (v == group){
            return
        }
        $("#group").append("<option value='"+v+"'>"+v+"</option>")
    })
    

}

$(document).ready(function(){
    getUsers()
})