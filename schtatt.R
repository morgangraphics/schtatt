if (!require("data.table")) {
  install.packages("data.table")
}
if (!require("lubridate")) {
  install.packages("lubridate")
}
if (!require("ggplot2")) {
  install.packages("ggplot2")
}
if (!require("scales")) {
  install.packages("scales")
}
if (!require("jsonlite")) {
  install.packages("jsonlite")
}

library(data.table)
library(lubridate)
library(ggplot2)
library(scales)
library(jsonlite)

message("Reading Data, may take a while")
#data <- fromJSON("min.data.json", flatten = FALSE)
data <- read.csv("test_data.csv", stringsAsFactors = FALSE)
message("Reading Data completed")

#json <- lapply(data, function(x) {
  #x[sapply(x, is.null)] <- NA
  #unlist(x)
#  sapply(x, function(y){
#    if (length(y) > 0 && y != 'NULL') {
#      print(y)
#    }
#  })
  
#})

#names(json)
#json[[1]][[1]][[2]]

#json <- lapply(data, function(x) {
#  x[sapply(x, is.null)] <- NA
#  #unlist(x)
#})



#foo <- do.call(rbind, json)

#foo[1]

#names(foo)

#vals <- lapply(data, fromJSON)

#res <- do.call(rbind, lapply(data, FUN=function(x){ as.list(x) }))
#res

#names(data)
#data[,1]

colorScheme <- c("cadetblue4", "azure4")


#Attempt to determine Timezone
tz <- unclass(as.POSIXlt(Sys.time()))

#Convert to a data table
dt <- data.table(data)

#Make Date Column a Date
dt$Date <- as.POSIXct(dt$Date, "%B %d, %Y %I:%M %p", tz="CDT")

#Format Date & Time into Usable Chunks
dt$xdate <- as.Date(format(dt$Date, "%Y-%m-%d"))
dt$xtime <-hour(dt$Date)
dt$xweek <-week(dt$Date)
dt$dow <- as.numeric(format(dt$Date, "%u"))

#Break down the earnings by Total, Max, Min and Average by day
stats.earnings.day <- dt[,list(total =  sum(Earnings, na.rm=TRUE), 
                               max.fare = max(Earnings, na.rm=TRUE), 
                               min.fare = min(Earnings, na.rm=TRUE), 
                               average.fare = mean(Earnings, na.rm=TRUE)), by=xdate]
setnames(stats.earnings.day, "xdate", "day")
setorder(stats.earnings.day, day)

#Break down the earnings by Total, Max, Min and Average by week
stats.earnings.week <- dt[,list(total =  sum(Earnings, na.rm=TRUE), 
                                max.fare = max(Earnings, na.rm=TRUE), 
                                min.fare = min(Earnings, na.rm=TRUE), 
                                average.fare = mean(Earnings, na.rm=TRUE)), by=dt$xweek]
setnames(stats.earnings.week, "dt", "week")
setorder(stats.earnings.week, week)

trips.per.day <- as.data.frame(table(dt$xdate))
colnames(trips.per.day) <- c("day", "trips")

milage.per.day <- dt[,list(mileage = sum(Mileage, na.rm=TRUE)), by=xdate]
setnames(milage.per.day, "xdate", "day")

stats.breakdown <- merge(trips.per.day, milage.per.day, by="day")



##HIGH LEVEL STUFF

#===================== Earning Distribution
#Shows where the largest and smallest earnings lie
earnings <- round(dt$Earnings, 1)
max(table(round(earnings, 0)))

p <- qplot(earnings, data=dt, binwidth = 1, geom="histogram", fill = ..count..) + scale_fill_continuous(name = "frequency", low=colorScheme[2], high=colorScheme[1])
p <- p + scale_y_continuous(breaks = 0:max(table(round(earnings, 0))))
p <- p + scale_x_continuous(breaks = 0:round(max(dt$Earnings), 0)) + theme_bw()
p <- p + labs(title="Distribution of Earnings", y = "frequency", x="Earnings (rounded to nearest 1/10 cent)")
print(p)

#===================== Earnings By DATE
# Calculates and plots the data by Date and highlights whether or not the day is Weekday vs. Weekend
earnings.by.date <- dt[,list(total = sum(Earnings, na.rm=TRUE)), by=xdate]

#Create Factor to distinguish Weekday from Weekend
weekend <- weekdays(as.Date(earnings.by.date$xdate)) %in% c("Friday", "Saturday", "Sunday")

#assign types
earnings.by.date$daytype <- "Weekday"
earnings.by.date$daytype[weekend == TRUE] <- "Weekend"

#coerce to factor for plotting
earnings.by.date$daytype <- as.factor(earnings.by.date$daytype)

str(earnings.by.date)

#Graph of Earnings to Date by Day
p <- ggplot(earnings.by.date, aes(xdate, total, group=daytype, fill=daytype)) + geom_bar(stat="identity") + theme_bw()
p <- p + scale_fill_manual(name="", values = alpha(colorScheme, .8)) + scale_x_date(breaks = earnings.by.date$xdate, labels = date_format("%b %d, %Y"))
p <- p + theme(axis.text.x = element_text(angle=90)) + labs(title="Earnings by Day", y = "", x="") 
print(p)



#===================== Earnings By TIME
#Calculates and plots the data by Time of Day and whether or not the time is AM vs PM
earnings.by.time <- dt[,list(total = sum(Earnings, na.rm=TRUE)), by=xtime]
pm <- earnings.by.time$xtime > 12

earnings.by.time$meridiem <- "AM"
earnings.by.time$meridiem[pm == TRUE] <- "PM"
earnings.by.time$meridiem <- as.factor(earnings.by.time$meridiem)

str(earnings.by.time)

#Graph of Earnings by Hour of Day
p <- ggplot(earnings.by.time, aes(xtime, total, group=meridiem, fill=meridiem)) + geom_bar(stat="identity") + theme_bw()
p <- p + scale_fill_manual(name="", values = alpha(colorScheme, .8)) + scale_x_continuous(breaks = 0:23) 
p <- p + labs(title="Earnings by Hour", y = "", x="")
#p <- p + theme(axis.text.x = element_text(angle=90))
print(p)

#===================== Earnings By DAY OF THE WEEK
earnings.by.dowk <- dt[,list(total = sum(Earnings, na.rm=TRUE)), by=dow]


#Create Factor to distinguish Weekday from Weekend
weekend <- earnings.by.dowk$dow %in% 5:7

#assign types
earnings.by.dowk$daytype <- "Weekday"
earnings.by.dowk$daytype[weekend == TRUE] <- "Weekend"

#coerce to factor for plotting
earnings.by.dowk$daytype <- as.factor(earnings.by.dowk$daytype)

#Graph of Earnings to Date by Day of the Week
q <- ggplot(earnings.by.dowk, aes(dow, total, fill=..count..))
q <- q + scale_fill_manual(name="", values = alpha(colorScheme, .8))
q <- q + geom_bar(stat="identity") + theme_bw() + labs(title="", y = "", x="")
q <- q + scale_x_discrete(limits=c("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday","Sunday"))
q <- q + labs(title="Earnings by Day of Week", y = "", x="") 
print(q)





#Break down the earnings by Total, Max, Min and Average by day
stats.earnings.day.time <- dt[,list(total =  sum(Earnings, na.rm=TRUE)), by=c("xdate","xtime")]

pm <- stats.earnings.day.time$xtime > 12

stats.earnings.day.time$meridiem <- "AM"
stats.earnings.day.time$meridiem[pm == TRUE] <- "PM"
stats.earnings.day.time$meridiem <- as.factor(stats.earnings.day.time$meridiem)


#Graph of Earnings to Date by Day
p <- ggplot(stats.earnings.day.time, aes(xtime, total, group=xdate, fill=meridiem), geom = "line") + geom_bar(stat="identity") + theme_bw()
#p <- p + scale_fill_continuous(name = "frequency", low=colorScheme[2], high=colorScheme[1])
p <- p + scale_fill_manual(name="", values = alpha(colorScheme, .8)) + scale_x_continuous(breaks = 0:23) 
p <- p + labs(title="Earnings by Hour", y = "", x="") + facet_wrap(~ xdate)
#p <- p + theme(axis.text.x = element_text(angle=90))
print(p)




#str(earnings.by.dowk)