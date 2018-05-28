function getIndustry(){
	$.getJSON("/internal/industry/getAllJobs", function(data){
		jobs = data.jobs
		translations = data.translations

		console.log(jobs)

		var d = new Date();
		var curTime = d.getTime()
		var offset = d.getTimezoneOffset() * 60 * 1000;

		$.each(jobs, function(k,v){
			var startTime = v.start_date - offset
			var endTime = v.end_date - offset
			var timeLeft = countDown(endTime)
			$(".industryList").append("\
								<tr>\
									<td><img src='https://image.eveonline.com/Type/"+v.blueprint_type_id+"_32.png'><br>"+translations[v.blueprint_type_id]+"</td>\
									<td><img src='https://image.eveonline.com/Character/"+v.installer_id+"_32.jpg'><br>"+translations[v.installer_id]+"</td>\
									<td>"+translations[v.location_id]+"</td>\
									<td>"+v.activity_id+"<br>Runs: "+v.runs+"/"+v.licensed_runs+"</td>\
									<td>"+convertDate(startTime)+"</td>\
									<td>"+convertDate(endTime)+"</td>\
									<td>"+timeLeft+" - "+v.status+"</td>\
								</tr>\
				")
		})
	})
}

function formatNumber(n, d){
	if(d){
		return n.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,');
	}
	return n.toFixed().replace(/(\d)(?=(\d{3})+(,|$))/g, '$1,')
}

function convertDate(epoch) {
	console.log(epoch)
    var date = new Date(epoch)
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    var hours = ('0' + date.getHours()).slice(-2);
    var minutes = ('0' + date.getMinutes()).slice(-2);
    var seconds = ('0' + date.getSeconds()).slice(-2);
    return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds
}

function countDown(epoch){
	var cur = (new Date).getTime()
	var diff = epoch - cur
	if (diff < 0){
		return "Done"
	}
	var milliseconds = parseInt((diff%1000)/100)
            , seconds = parseInt((diff/1000)%60)
            , minutes = parseInt((diff/(1000*60))%60)
            , hours = parseInt((diff/(1000*60*60)));

        hours = (hours < 10) ? "0" + hours : hours;
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        seconds = (seconds < 10) ? "0" + seconds : seconds;

        return hours + "H " + minutes + "M"
}

$(document).ready(function(){
	getIndustry()
})