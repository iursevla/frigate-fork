import datetime
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs/{service}")
def logs(
    service: str,
    download: Optional[str] = None,
    start: Optional[int] = 0,
    end: Optional[int] = 0,
):
    def download_logs(service_location: str):
        try:
            file = open(service_location, "r")
            contents = file.read()
            file.close()
            return JSONResponse(jsonable_encoder(contents))
        except FileNotFoundError as e:
            logger.error(e)
            return JSONResponse(
                content={"success": False, "message": "Could not find log file"},
                status_code=500,
            )

    log_locations = {
        "frigate": "/dev/shm/logs/frigate/current",
        "go2rtc": "/dev/shm/logs/go2rtc/current",
        "nginx": "/dev/shm/logs/nginx/current",
        "chroma": "/dev/shm/logs/chroma/current",
    }
    service_location = log_locations.get(service)

    if not service_location:
        return JSONResponse(
            content={"success": False, "message": "Not a valid service"},
            status_code=404,
        )

    if download:
        return download_logs(service_location)

    # start = request.args.get("start", type=int, default=0)
    # end = request.args.get("end", type=int)

    try:
        file = open(service_location, "r")
        contents = file.read()
        file.close()

        # use the start timestamp to group logs together``
        logLines = []
        keyLength = 0
        dateEnd = 0
        currentKey = ""
        currentLine = ""

        for rawLine in contents.splitlines():
            cleanLine = rawLine.strip()

            if len(cleanLine) < 10:
                continue

            # handle cases where S6 does not include date in log line
            if "  " not in cleanLine:
                cleanLine = f"{datetime.now()}  {cleanLine}"

            if dateEnd == 0:
                dateEnd = cleanLine.index("  ")
                keyLength = dateEnd - (6 if service_location == "frigate" else 0)

            newKey = cleanLine[0:keyLength]

            if newKey == currentKey:
                currentLine += f"\n{cleanLine[dateEnd:].strip()}"
                continue
            else:
                if len(currentLine) > 0:
                    logLines.append(currentLine)

                currentKey = newKey
                currentLine = cleanLine

        logLines.append(currentLine)

        return JSONResponse(
            content={"totalLines": len(logLines), "lines": logLines[start:end]},
            status_code=200,
        )
    except FileNotFoundError as e:
        logger.error(e)
        return JSONResponse(
            content={"success": False, "message": "Could not find log file"},
            status_code=500,
        )
